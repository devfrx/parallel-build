---
name: parallel-build
description: Costruzione in parallelo di un'app progettata con app-blueprint — i giorni 2 e 3 del metodo. Controllo preliminare dell'ambiente, scheletro, oracoli scritti prima del codice, esemplari per archetipo, ondate di sotto-agenti in worktree isolati, rientro seriale verificato da comandi, end-to-end, revisione, production readiness review e report che separa verificato e dedotto. Usa questa skill OGNI VOLTA che esiste un piano validato da app-blueprint e l'utente vuole passare alla costruzione — "costruiamo", "partiamo con il giorno 2", "lancia le ondate", "esegui il piano", "riprendiamo la costruzione", "chiudiamo la build" — e quando bisogna riprendere o chiudere una costruzione in corso. NON usarla senza un piano validato (prima app-blueprint), per singole feature su codice esistente (dev-discipline), né per lavoro che non si divide in moduli con proprietà disgiunta.
---

# Parallel Build

Questa skill governa i giorni 2 e 3 del metodo di costruzione parallela: trasforma il piano di `app-blueprint` in un'applicazione funzionante, con più sotto-agenti di Claude Code al lavoro contemporaneamente.

Il piano ha risolto chi fa cosa. Restano i problemi che nascono quando gli agenti lavorano davvero:

- i sotto-agenti non possono fare domande all'utente;
- scrivono in parallelo sullo stesso repository;
- dichiarano risultati che non sempre sono veri;
- ripetono in parallelo lo stesso errore.

Il principio di fondo: **la parte parallela è economica, quella seriale decide la qualità e la velocità.** Dieci agenti scrivono in un'ora ciò che un agente scrive in dieci; ma tutto ciò che scrivono rientra, uno alla volta, da una porta stretta. Quella porta va resa veloce e inflessibile: veloce perché è il collo di bottiglia, inflessibile perché è l'unico punto in cui un errore si ferma prima di propagarsi.

**Prerequisiti.** Questa skill si appoggia a skill che governano aspetti qui non ripetuti:

- `app-blueprint` — il piano validato, i contratti congelati, gli ADR. Senza questi, la skill non parte.
- `decision-principles` — la delega: brief, copie isolate, integrazione seriale, verificato contro dedotto.
- `dev-discipline` — il codice dentro ogni task (gli agenti la hanno precaricata).
- `dev-communication` — quando fermarsi. Qui prende la forma delle escalation.
- `frontend-craft` — l'interfaccia, precaricata nel `frontend-builder` e usata dalla lente UI della revisione.
- `design-docs` — la documentazione come parte della Definition of Done.
- `lean-docs` — il `CLAUDE.md` snello: ogni sotto-agente lo carica, quindi il suo peso si moltiplica per il numero di agenti.
- `session-handoff` / `session-resume` — tra un giorno e l'altro.
- `compliance-docs` — in chiusura, se l'app tratta dati personali.

Leggile se non sono già in contesto.

## Le tre regole che governano tutto

In caso di tensione tra qualsiasi indicazione di questa skill, vincono queste tre, in quest'ordine:

1. **Si scrive in copie isolate, si rientra in serie, e il rientro lo verificano i comandi.** Ogni sotto-agente che scrive lavora nel proprio worktree. Nel branch d'integrazione entra un ramo alla volta, e solo dopo che tre cose sono passate: la validazione del suo esito, la verifica della sua ownership, i gate rieseguiti dall'orchestratore. L'esito del sotto-agente è una dichiarazione; un comando verde è un fatto.
2. **L'oracolo non si tocca.** I costruttori fanno passare test scritti da altri, prima di loro. Un costruttore che ritiene sbagliato un test lo segnala come escalation, non lo modifica. Non lo modifica nemmeno l'orchestratore durante il rientro: un test cambiato per farlo passare è un test che ha smesso di misurare.
3. **Un errore ripetuto è a monte.** Se la stessa causa fa fallire due o più task, la causa sta nel contratto, nell'esemplare, nell'oracolo o nel brief. Si ferma l'ondata, si corregge a monte, si riparte. Correggerlo N volte a valle produce N correzioni diverse. Per lo stesso motivo un task ha al massimo due tentativi di correzione; poi diventa un'escalation.

## Gli agenti

Definiti a livello di plugin (vedi il README del pacchetto), ognuno con il minimo privilegio che il suo ruolo richiede:

| Agente | Quando | Strumenti | Skill precaricate | Isolamento |
|---|---|---|---|---|
| `researcher` | giorno 1 | WebSearch, WebFetch, Read, Grep, Glob | decision-principles | non scrive |
| `test-author` | oracoli, e2e | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline | worktree |
| `backend-builder` | costruzione, spike | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline | worktree |
| `frontend-builder` | costruzione, spike | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline, frontend-craft | worktree |
| `reviewer` | revisione | Read, Grep, Glob, Bash | decision-principles, dev-discipline, frontend-craft | worktree |

Due regole su come si lanciano, entrambe verificate sulla documentazione di Claude Code (ottobre 2026):

- **Passa sempre l'isolamento in worktree nella chiamata stessa, e non dare nomi ai sotto-agenti.** Con gli agent teams attivi, un sotto-agente lanciato con un nome diventa un teammate e lavora nella directory principale. L'isolamento scritto nel frontmatter non lo impedisce; solo quello passato nella chiamata sì. Per riprendere un agente usa l'id che ricevi al suo completamento.
- **I worktree partono dal branch di default remoto**, a meno che `worktree.baseRef` sia `"head"`. Senza questa impostazione i costruttori non vedrebbero né lo scheletro né gli esemplari. La imposta e la verifica il controllo preliminare.

## Workflow

### Fase 0 — Controllo preliminare

Leggi `references/preflight.md` ed esegui ogni controllo. Alcuni sono funzionali: un sotto-agente di prova dimostra che parte dalla base giusta, che ha le skill precaricate e che una ripresa torna nel suo worktree. Se un controllo fallisce, la costruzione non parte: un problema d'ambiente scoperto durante un'ondata costa dieci volte tanto. Registra l'esito con `scripts/registro.py` (evento `preflight`).

### Fase 1 — Scheletro e spike

Leggi `references/ondata-zero.md`. La sessione principale costruisce lo scheletro: tutto ciò che è condiviso, creato una volta e congelato. Comprende:

- tooling e CI con i comandi del piano e i gate di supply chain;
- migrazioni dall'ER e kernel condiviso (autenticazione, autorizzazioni dalla matrice, errori, log);
- codice generato dalla specifica, mock con interruttore verso il reale;
- shell dell'interfaccia con token e componenti base;
- registri con gli stub di tutti i moduli, facciate stub, fitness function, generatori, dati sintetici;
- l'elenco dei moduli in attesa, i cui oracoli la suite esclude finché non rientrano;
- isolamento dei test in parallelo: database, porte e cartelle temporanee per esecuzione, perché i worktree isolano i file, non i processi;
- `CLAUDE.md` snello.

In parallelo, gli spike del piano girano in copie usa e getta. Se uno spike smentisce un'assunzione, ci si ferma: si torna all'ADR con l'utente prima di scrivere un solo oracolo.

Lo scheletro è finito quando ogni comando del piano gira, e passa sullo scheletro vuoto. A quel punto:

1. i diagrammi di ciò che ora esiste passano dagli ADR a `docs/design/`;
2. si attivano le regole di deny su installazioni e push;
3. si committa e si applica il tag `build/scheletro`.

### Fase 2 — Oracoli

Un `test-author` per modulo, in parallelo, secondo i task `oracoli` del piano. Scrivono test d'accettazione per storia, di contratto, di autorizzazione dalla matrice, e d'interfaccia con selettori per ruolo e nome accessibile. Ogni test deve essere **rosso per la ragione giusta**: fallisce su un'asserzione o su "non implementato", non su un errore di sintassi o di import. Il rientro segue `references/rientro.md`. Per gli oracoli l'orchestratore esegue i test e controlla il tipo di fallimento. Tag `build/oracoli`.

### Fase 3 — Esemplari, prova a secco, gate 2

Sempre in `references/ondata-zero.md`. La sessione costruisce un esemplare per archetipo, completo e verde contro i suoi oracoli, e ne ricava i generatori.

Poi la **prova a secco**: un costruttore nuovo aggiunge un modulo usa e getta usando solo `CLAUDE.md`, esemplare e generatori. Se sbaglia, la documentazione o i generatori vanno corretti prima che lo stesso errore si moltiplichi per dieci.

Seguono il gate eseguibile completo e il **gate 2** con l'utente, guidato da `assets/brief-gate-2.md`. Tag `build/gate-2`. A fine giornata, `session-handoff`.

### Fase 4 — Costruzione e rientro

Leggi `references/delega-ed-esito.md` e `references/rientro.md`. Lancia i task dell'ondata `costruzione`, entro il limite di concorrenza, ciascuno con il brief di `assets/brief-costruttore.md`. Ogni costruttore lavora contro oracoli già scritti, parte dal generatore del suo archetipo, e chiude scrivendo il file d'esito.

I rami rientrano uno alla volta, man mano che arrivano:

1. `valida_esito.py` e `verifica_ownership.py` sul ramo;
2. controllo dei trailer di co-autore nei commit;
3. merge senza commit, rimozione della voce del task dall'elenco dei moduli in attesa, gate incrementale, poi commit oppure annullamento.

Quando un modulo backend rientra verde, il suo frontend passa dal mock al reale. I fallimenti tornano al proprietario, per al massimo due tentativi. Le cause si contano, per far scattare l'interruttore sistemico. Le escalation non bloccanti si raccolgono e si portano all'utente a fine ondata. Chiude l'ondata la suite completa più la CI. Tag `build/costruzione`.

### Fase 5 — End-to-end

Un `test-author` per percorso critico, sull'app integrata. Qui un test rosso non è atteso: è un difetto, e torna al proprietario del modulo attraverso lo stesso rientro. L'autore del test non corregge l'app. Suite completa. Tag `build/e2e`.

### Fase 6 — Revisione

Leggi `references/revisione-e-chiusura.md`. Tre `reviewer` in parallelo, uno per lente: sicurezza, coerenza, interfaccia. Lavorano in sola lettura e producono findings con severità P0–P3 e posizione `file:riga`. L'orchestratore li verifica e li deduplica, e le correzioni tornano ai proprietari attraverso il rientro. Per i moduli ad alto rischio la lente di sicurezza è obbligatoria e approfondita, e l'utente guarda il diff.

### Fase 7 — Chiusura, consegna, retrospettiva

Sempre in `references/revisione-e-chiusura.md`:

1. gate finale e production readiness review (`assets/prr-checklist.md`);
2. matrice di tracciabilità storie → test → esito;
3. test di manutenibilità;
4. documentazione allineata (`design-docs`, README, runbook) e `compliance-docs` se servono;
5. report di consegna (`assets/report-consegna.md`), che separa verificato, dedotto e non verificato;
6. pulizia di worktree e rami;
7. retrospettiva dal registro.

## Protocolli trasversali

**Registro.** Ogni evento significativo passa da `scripts/registro.py` in `.build/registro.jsonl`: deleghe, rientri riusciti e falliti con la causa, escalation, interruttori, gate, decisioni. È ciò che rende misurabili la giornata, il report e la retrospettiva.

**Checkpoint.** Il branch d'integrazione è sempre verde, perché il merge si committa solo dopo il gate. "Verde" esclude solo gli oracoli dei moduli in attesa, e l'elenco si svuota man mano che i moduli rientrano. Ogni merge commit è un punto di ripristino, e un tag `build/<fase>` segna ogni stato verde di fine fase. Si torna indietro di un'ondata con un comando, non con un'archeologia.

**Escalation.** Il sotto-agente non chiede, scrive la domanda nel suo esito, con le opzioni e la sua raccomandazione.

- Bloccante: cambiare un contratto, aggiungere una dipendenza, toccare un intoccabile, contestare un oracolo, colmare un requisito ambiguo che cambia il comportamento. Ferma solo il suo task.
- Non bloccante: si raccoglie e si porta all'utente in blocco a fine ondata.

Una risposta che tocca una decisione strutturale aggiorna un ADR.

**Cambiamento.**

- Una richiesta nuova a costruzione avviata va in `.build/backlog.md`, per la versione successiva.
- Un cambio di contratto parte da un'analisi d'impatto (quali task, oracoli e mock tocca) e passa per una decisione dell'utente.
- Un componente condiviso che emerge resta locale al modulo e viene segnalato come candidato alla promozione. La promozione avviene in un task seriale, dopo l'ondata.

**Tra un giorno e l'altro.** Lo stato vive su disco: piano, registro, tag, esiti. A fine giornata `session-handoff`, all'inizio `session-resume`.

## Definition of Done

L'app è "completa" quando:

- le storie `must` hanno i test d'accettazione verdi;
- i test di contratto, autorizzazione e fitness sono verdi;
- l'elenco dei moduli in attesa è vuoto, quindi nessun oracolo è escluso dalla suite;
- i percorsi critici end-to-end sono verdi;
- la CI è verde sul branch d'integrazione;
- la documentazione descrive ciò che esiste;
- la production readiness review è compilata, con ogni voce verificata oppure dichiarata non verificabile in locale;
- il report separa ciò che è verificato da ciò che è dedotto.

"Completa" non significa "provata in produzione", e il report lo dice.

## Casi edge

- **Limiti d'uso raggiunti a metà ondata.** L'ondata si ferma e riprende quando i limiti lo consentono; il registro lo mostra. La giornata si allunga: non si recupera tempo abbassando i controlli.
- **Un sotto-agente finisce senza file d'esito.** Riprendilo chiedendo l'esito. Se non è possibile, tratta il ramo come `parziale` e verifica tutto da zero.
- **Conflitto di merge.** Non si risolve "con creatività": con ownership disgiunta un conflitto è un accoppiamento che il piano non ha visto. Annulla il merge, capisci quale file condiviso o quale errore di piano l'ha prodotto, correggi il piano, poi rilancia.
- **Un oracolo è davvero sbagliato.** Decide l'utente. La correzione la fa un `test-author` in un task dedicato, registrata come cambiamento: mai il costruttore, mai l'orchestratore durante un merge.
- **Il gate incrementale è lento.** È la parte seriale: ottimizzalo (solo i test dei moduli toccati, cache, parallelismo del test runner) prima di continuare. Saltarlo non è un'ottimizzazione.
- **L'utente chiede di saltare il controllo preliminare o un gate.** Dì prima cosa si perde e proponi l'alternativa sicura più economica. Se l'utente decide comunque, registra la decisione e marca come "non verificato" nel report ciò che quel gate avrebbe verificato.
- **Più task della concorrenza disponibile.** L'ondata procede a lotti: si lancia il successivo man mano che i precedenti rientrano.

## Cosa NON fare

- Non lanciare un'ondata con il controllo preliminare fallito, o con il checkout principale sporco: i worktree partono dal commit, non dai file non committati.
- Non dare nomi ai sotto-agenti, e non contare solo sull'isolamento scritto nel frontmatter.
- Non accettare un ramo perché il suo esito dice "completato": riesegui i gate.
- Non modificare un oracolo per far passare un rientro, né lasciarlo modificare a un costruttore.
- Non risolvere un conflitto di merge a mano dentro il rientro.
- Non correggere a valle, N volte, un errore che ha una causa a monte.
- Non installare dipendenze né toccare intoccabili durante le ondate: sono escalation.
- Non lasciare commit con trailer di co-autore.
- Non dichiarare "completa" un'app la cui production readiness review ha voci non verificate e taciute.

## Checklist prima della consegna

1. Il controllo preliminare è registrato come passato, e ogni ondata ha il suo tag verde?
2. Ogni ramo è rientrato con esito valido, ownership verificata e gate rieseguiti?
3. Gli oracoli sono intatti dal loro rientro, salvo cambiamenti decisi dall'utente e registrati?
4. Le storie `must` sono tutte verdi nella matrice di tracciabilità, e l'elenco dei moduli in attesa è vuoto?
5. I findings P0 e P1 della revisione sono chiusi, o accettati esplicitamente dall'utente?
6. La production readiness review è compilata con prove, e il non verificabile in locale è dichiarato?
7. `docs/design/` descrive ciò che esiste, e gli ADR hanno lo stato giusto?
8. Il report separa verificato, dedotto e non verificato, e riporta le metriche del registro?
9. Worktree e rami dei task sono puliti, e il registro è archiviato?

Se una risposta è "no", sistemala o dichiarala nel report.
