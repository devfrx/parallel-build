---
name: parallel-build
description: Costruzione in parallelo di un incremento progettato e congelato con app-blueprint — ambienti e walking skeleton, poi implementazione, integrazione, verifica, accettazione e rilascio come fasi con gate (voci 7.09–12 della checklist), con oracoli scritti prima del codice, motore ed esemplari, ondate di sotto-agenti in worktree isolati, rientro seriale verificato da comandi, revisione per lenti e report che separa verificato e dedotto. Usa questa skill OGNI VOLTA che app-blueprint ha congelato un incremento e l'utente vuole costruirlo — "costruiamo", "lancia le ondate", "esegui il piano", "riprendiamo la costruzione", "chiudiamo l'incremento", "rilasciamo" — e quando bisogna riprendere o chiudere una costruzione in corso. NON usarla senza un incremento congelato (prima app-blueprint), per singole feature su codice esistente (dev-discipline), né per lavoro che non si divide in moduli con proprietà disgiunta.
---

# Parallel Build

Questa skill costruisce un incremento progettato con `app-blueprint`, con più sotto-agenti di Claude Code al lavoro contemporaneamente, ed esegue le fasi della checklist che vengono dopo il congelamento: ambienti e scheletro (7.09, 7.10), implementazione (8), integrazione (9), verifica (10), validazione e accettazione (11), rilascio (12). Si ripete a ogni incremento.

Il progetto ha risolto chi fa cosa. Restano i problemi che nascono quando gli agenti lavorano davvero:

- i sotto-agenti non possono fare domande all'utente;
- scrivono in parallelo sullo stesso repository;
- dichiarano risultati che non sempre sono veri;
- ripetono in parallelo lo stesso errore.

Il principio di fondo: **la parte parallela è economica, quella seriale decide la qualità e la velocità.** Dieci agenti scrivono insieme ciò che un agente scrive in sequenza; ma tutto ciò che scrivono rientra, uno alla volta, da una porta stretta. Quella porta va resa veloce e inflessibile: veloce perché è il collo di bottiglia, inflessibile perché è l'unico punto in cui un errore si ferma prima di propagarsi.

**Prerequisiti.** Un incremento congelato: `progetto.py verifica --congelamento stato` verde, con lo script di `app-blueprint` (`python <cartella di app-blueprint>/scripts/progetto.py`, eseguito dalla radice del repo). Skill su cui questa si appoggia, senza ripeterle: `app-blueprint` (sorgenti, comandi, protocollo di punti e fasi, gestione delle modifiche), `decision-principles` (la delega), `dev-discipline` e `lean-code` (il codice dentro ogni task), `dev-communication` (quando fermarsi: qui prende la forma delle escalation), `frontend-craft` (l'interfaccia e la sua revisione), `lean-docs` (il `CLAUDE.md` snello), `compliance-docs` (conformità), `session-resume` e `session-handoff`. Leggile se non sono già in contesto.

## Le tre regole che governano tutto

In caso di tensione tra qualsiasi indicazione di questa skill, vincono queste tre, in quest'ordine:

1. **Si scrive in copie isolate, si rientra in serie, e il rientro lo verificano i comandi.** Ogni sotto-agente che scrive lavora nel proprio worktree. Nel branch d'integrazione entra un ramo alla volta, e solo dopo che tre cose sono passate: la validazione del suo esito, la verifica della sua ownership, i gate rieseguiti dall'orchestratore. L'esito del sotto-agente è una dichiarazione; un comando verde è un fatto.
2. **L'oracolo non si tocca.** I costruttori fanno passare test scritti da altri, prima di loro. Un costruttore che ritiene sbagliato un test lo segnala come escalation, non lo modifica. Non lo modifica nemmeno l'orchestratore durante il rientro: un test cambiato per farlo passare è un test che ha smesso di misurare.
3. **Un errore ripetuto è a monte.** Se la stessa causa fa fallire due o più task, la causa sta nel contratto, nell'esemplare, nell'oracolo o nel brief. Si ferma l'ondata, si corregge a monte, si riparte. Correggerlo N volte a valle produce N correzioni diverse. Per lo stesso motivo un task ha al massimo due tentativi di correzione; poi diventa un'escalation.

## Gli agenti

Li installa `app-blueprint` alla voce 0.03, in `.claude/agents/` del progetto; possono anche venire da un plugin o da `~/.claude/agents/`. Ognuno ha il minimo privilegio che il suo ruolo richiede:

| Agente | Quando | Strumenti | Skill precaricate | Isolamento |
|---|---|---|---|---|
| `test-author` | oracoli, end-to-end | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline, lean-code | worktree |
| `backend-builder` | costruzione, correzioni | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline, lean-code | worktree |
| `frontend-builder` | costruzione, correzioni | Read, Write, Edit, Bash, Glob, Grep | decision-principles, dev-discipline, lean-code, frontend-craft | worktree |
| `reviewer` | revisione per lenti | Read, Grep, Glob, Bash | decision-principles, dev-discipline, frontend-craft, design-docs | worktree |
| `researcher` | riverifiche, se servono | WebSearch, WebFetch, Read, Grep, Glob | decision-principles | non scrive |

Due regole su come si lanciano:

- **Passa sempre l'isolamento in worktree nella chiamata stessa, e non dare nomi ai sotto-agenti.** Con gli agent teams attivi, un sotto-agente lanciato con un nome diventa un teammate e lavora nella directory principale; l'isolamento scritto nel frontmatter non lo impedisce, solo quello passato nella chiamata sì. Per riprendere un agente usa l'id che ricevi al suo completamento.
- **I worktree partono dal branch di default del remoto**, a meno che `worktree.baseRef` sia `"head"`. Senza questa impostazione i costruttori non vedrebbero né lo scheletro né gli esemplari. La imposta `app-blueprint` alla 0.02 e la verifica il controllo preliminare.

## Fasi, punti e gate

La costruzione usa il protocollo di `app-blueprint`, sullo stesso registro: ogni voce si apre e si chiude con `progetto.py apri` e `progetto.py chiudi --evidenza …`, ogni fase finisce con `verifica --gate N`, il brief all'utente, la sua approvazione e `progetto.py approva N`. Le voci delle fasi 8–12 si richiudono a ogni incremento, e i comandi registrano l'incremento da soli. `progetto.py checklist --fase N` dice quali voci valgono per il profilo. In più, `scripts/registro.py` tiene in `.build/registro.jsonl` gli eventi operativi della costruzione: deleghe, rientri, cause, escalation, interruttori.

| Voci | Reference | Cosa |
|---|---|---|
| 7.09, 7.10 e gate 7 | `preflight.md`, `scheletro.md` | controllo preliminare, ambienti, walking skeleton; poi il gate della fase 7 con l'utente |
| 8 | `costruzione.md`, `delega-ed-esito.md`, `rientro.md` | oracoli, motore, esemplari, prova a secco e approvazione degli esemplari, ondate di costruzione con il rientro, controlli sull'intera base di codice |
| 9–12 | `verifica-e-rilascio.md` | integrazione ed end-to-end, revisione per lenti e verifiche, accettazione dell'utente, rilascio secondo il profilo, report, pulizia, retrospettiva |

Ogni stato verde di fine tappa porta un tag `build/incremento-<n>/<tappa>`: si torna indietro di un'ondata con un comando, non con un'archeologia.

**Il brief di ogni task** è la parte comune di `assets/brief-costruttore.md` più `progetto.py fascio --task <id>`, che assembla dalle sorgenti esattamente ciò che il task deve leggere ed elenca a parte ciò che è progettato per incrementi futuri e non si costruisce ora.

**La DoD di incremento** è quella del catalogo, filtrata dal profilo (`progetto.py checklist --dod`): le voci di livello `task` si verificano a ogni rientro, quelle di livello `incremento` alla chiusura della fase 8 (voce 8.01).

## Protocolli trasversali

**Checkpoint.** Il branch d'integrazione è sempre verde, perché il merge si committa solo dopo il gate. "Verde" esclude solo gli oracoli dei moduli in attesa, e l'elenco si svuota man mano che i moduli rientrano (voce 8.13). Ogni merge commit è un punto di ripristino.

**Escalation.** Il sotto-agente non chiede: scrive la domanda nel suo esito, con le opzioni e la sua raccomandazione.

- Bloccante: cambiare un contratto, aggiungere una dipendenza, toccare un intoccabile, contestare un oracolo, colmare un requisito ambiguo che cambia il comportamento. Ferma solo il suo task.
- Non bloccante: si raccoglie e si porta all'utente in blocco a fine ondata.

**Cambiamento.** Ogni cambio di ciò che è congelato — contratto, oracolo, scope — è una modifica di `app-blueprint` (`MOD-n`, con l'analisi d'impatto e la decisione dell'utente), che annulla il congelamento: si lavorano le voci riaperte, si ricongela, e solo allora i task coinvolti incorporano il cambio (`rientro.md`). Una richiesta nuova a costruzione avviata si registra come modifica proposta e si valuta all'apertura dell'incremento successivo: lo scope congelato è ciò che rende possibile il parallelismo.

**Tra una sessione e l'altra.** Lo stato vive su disco: registro dei gate, piano, registro di build, tag, esiti. A fine sessione `session-handoff`, all'inizio `session-resume` e `progetto.py stato`.

## Casi limite

- **Limiti d'uso raggiunti a metà ondata.** L'ondata si ferma e riprende quando i limiti lo consentono; il registro lo mostra. Non si recupera tempo abbassando i controlli.
- **Un sotto-agente finisce senza file d'esito.** Riprendilo chiedendo l'esito. Se non è possibile, tratta il ramo come `parziale` e verifica tutto da zero.
- **Conflitto di merge.** Con ownership disgiunta un conflitto è un accoppiamento che il piano non ha visto. Annulla il merge, trova quale file condiviso o quale errore di piano l'ha prodotto, correggi a monte, poi rilancia.
- **Un oracolo è davvero sbagliato.** Decide l'utente, con una modifica. La correzione la fa un `test-author` in un task dedicato: mai il costruttore, mai l'orchestratore durante un merge.
- **Il gate incrementale è lento.** È la parte seriale: ottimizzalo (solo i test del modulo toccato, cache, parallelismo del test runner) prima di continuare. Saltarlo non è un'ottimizzazione.
- **L'utente chiede di saltare il controllo preliminare o un gate.** Dì prima cosa si perde e proponi l'alternativa sicura più economica. Se l'utente decide comunque, la voce si chiude come non applicabile con il suo motivo e la sua approvazione, e il report la elenca tra il non verificato.
- **Più task della concorrenza disponibile.** L'ondata procede a lotti: si lancia il successivo man mano che i precedenti rientrano.

## Cosa NON fare

- Non partire senza un incremento congelato, con il controllo preliminare fallito o con il checkout principale sporco: i worktree partono dal commit, non dai file non committati.
- Non dare nomi ai sotto-agenti, e non contare solo sull'isolamento scritto nel frontmatter.
- Non accettare un ramo perché il suo esito dice "completato": riesegui i gate.
- Non modificare un oracolo per far passare un rientro, né lasciarlo modificare a un costruttore.
- Non risolvere un conflitto di merge a mano dentro il rientro, e non correggere a valle, N volte, un errore che ha una causa a monte.
- Non installare dipendenze né toccare intoccabili durante le ondate: sono escalation.
- Non costruire ciò che il fascio elenca per incrementi futuri.
- Non lasciare commit con trailer di co-autore.
- Non chiudere una voce senza evidenza, né approvare un gate senza il sì esplicito dell'utente, né dichiarare consegnato ciò che il report non può dimostrare.
