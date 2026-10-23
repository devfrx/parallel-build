# Revisione e chiusura

La revisione cerca ciò che i test non possono vedere. La chiusura dimostra ciò che si può dimostrare e dichiara il resto. Nessuna delle due aggiunge funzionalità.

## Revisione

### Tre lenti, tre reviewer

Tre `reviewer` in parallelo sull'app integrata, ciascuno con una lente. Lavorano in sola lettura: possono eseguire comandi per raccogliere prove (test, analizzatori), non modificare file.

**Sicurezza.**
- La matrice delle autorizzazioni contro il codice: ogni regola è applicata nel backend, nessuna operazione sfugge al kernel, le condizioni di proprietà valgono anche per gli id passati nell'URL o nel corpo.
- Validazione degli input ai confini di fiducia, segreti nel codice o nei log, dati personali nei log.
- Risultati dei gate di supply chain.
- Le minacce del threat model: per ognuna, la contromisura c'è?

Per i moduli ad alto rischio la lente è obbligatoria e va letta riga per riga, non per campione.

**Coerenza.**
- Aderenza agli esemplari, convenzioni del repo, gestione degli errori uniforme.
- Duplicazione tra moduli: candidati alla promozione mancati.
- Confini che le fitness function non vedono, come accoppiamenti attraverso dati o configurazione.
- Prestazioni del backend: query ripetute per ogni elemento, query senza indice sui percorsi critici, elenchi senza limite.

**Interfaccia.** Con il metodo di revisione di `frontend-craft`: gerarchia, stati, accessibilità WCAG 2.2 AA, prestazioni, aderenza ai mockup e ai token.

### Findings

Formato unico, una riga per finding, come in `frontend-craft`:

```
percorso/file.ext:riga [P1] cosa non va — prova (comando, output, regola violata)
```

Severità:

| Livello | Significato |
|---|---|
| **P0** | Blocca una storia `must`, espone dati o denaro, o causa perdita di dati |
| **P1** | Difetto serio: viola un contratto, la matrice, un requisito misurato o WCAG AA |
| **P2** | Fastidio o costo di manutenzione con una via d'uscita |
| **P3** | Rifinitura |

Un finding senza prova è un'ipotesi: il reviewer lo marca come dedotto.

### Dai findings alle correzioni

L'orchestratore:

1. **Deduplica** i findings, perché le lenti si sovrappongono.
2. **Verifica** i P0 e i P1 prima di agire: riproduce la prova, o la fa riprodurre. Un finding falso costa una correzione inutile e, a volte, un difetto nuovo.
3. **Assegna** ogni correzione al proprietario del percorso secondo il piano: ripresa o rilancio, come nel ciclo di correzione. Un finding che richiede di cambiare un contratto o un oracolo passa dalla gestione del cambiamento.
4. **Fa rientrare** le correzioni con la procedura normale.

P0 e P1 si chiudono prima della consegna, o l'utente li accetta esplicitamente come rischio, con la motivazione nel report. P2 e P3 vanno nel backlog, salvo correzioni banali.

Tag `build/revisione`.

## Chiusura

### 1. Gate finale

Ogni comando del piano, compresi `suite`, `e2e` e `supply_chain`, verde sul branch d'integrazione, e CI verde. **L'elenco dei moduli in attesa è vuoto**: se contiene ancora voci, ci sono oracoli esclusi dalla suite, e "verde" non significa ciò che sembra.

### 2. Production readiness review

Compila `assets/prr-checklist.md` in `.build/prr.md`. Ogni voce ha uno di tre stati, e una prova:

- **verificato**: il comando eseguito, il file, il test;
- **non verificabile in locale**: si dice perché, e cosa servirà per verificarlo (per esempio un ripristino da backup provato solo in staging);
- **non applicabile**: si dice perché.

Una voce senza stato non è "probabilmente a posto": è aperta.

### 3. Tracciabilità

La matrice storie → test → esito, ricavata dai risultati dei test tramite gli id delle storie nei nomi o nelle annotazioni:

| Storia | Priorità | Test d'accettazione | End-to-end | Esito |
|---|---|---|---|---|

Ogni storia `must` è verde. Una storia `should` o `could` senza test è dichiarata "non verificata", non omessa.

### 4. Test di manutenibilità

Lo stesso esercizio della prova a secco, sull'app finita. Un costruttore nuovo aggiunge un modulo usa e getta usando solo la documentazione del repo. Se ci riesce seguendo i pattern, la documentazione regge chi verrà dopo. Altrimenti si corregge la documentazione, non si annota il problema. Il ramo non rientra, e si cancella.

### 5. Documentazione

- **`design-docs`**: `docs/design/` descrive ciò che esiste. I diagrammi di destinazione degli ADR ormai realizzati sono passati lì. Gli ADR hanno lo stato giusto.
- **README e runbook**: avvio, test, deploy, rollback, ripristino da backup, dove guardare quando qualcosa va storto (le convenzioni di osservabilità decise il giorno 1).
- **`CLAUDE.md`**: le regole per gli agenti valide durante la costruzione (ownership, elenco d'attesa) diventano quelle per il lavoro ordinario. Con `lean-docs`, il file resta snello.
- **`compliance-docs`**, se l'app tratta dati personali: le bozze preparate il giorno 1 si completano con ciò che l'app fa davvero, e vanno fatte rivedere a un professionista prima del lancio.

### 6. Report di consegna

Scrivi `.build/report.md` con `assets/report-consegna.md`. Il report separa ciò che è verificato (eseguito, con prova), ciò che è dedotto, e ciò che non è verificato. Riporta inoltre le escalation aperte, il backlog, i rischi accettati e le metriche del registro (`scripts/registro.py riepilogo`). Un report che sembra più completo di quanto sia è debito che matura sul primo che costruisce sopra.

### 7. Pulizia

- **Worktree dei task**: per ognuno, controlla con `git status` che non contenga lavoro non rientrato, poi `git worktree remove`. Con le cartelle collegate (`symlinkDirectories`) git rifiuta senza `--force`: usalo solo dopo il controllo.
- **Rami dei task**: `git branch -d`, che rifiuta i rami non mergiati. Un rifiuto è un'informazione, non un ostacolo da forzare. I rami degli spike e delle prove a secco, non mergiati per costruzione, si cancellano con `-D`, controllando il nome uno per uno.
- **Regole di deny temporanee**: si tolgono, se l'utente non vuole tenerle.
- **`.build/`**: il registro e il report si archiviano fuori dal repo, perché servono alla retrospettiva e al banco di prova. Chiedi all'utente dove. Poi la cartella si elimina.

### 8. Consegna

Il report all'utente, con in testa ciò che deve sapere subito: rischi accettati, voci non verificabili in locale, escalation aperte. Si consegna ciò che il report descrive, non ciò che il piano prometteva.

## Retrospettiva

Dal registro, non dalla memoria:

- **dove è andato il tempo**: durata per ondata, tempo nel rientro contro tempo dei sotto-agenti;
- **quante volte un task è tornato indietro**, e per quali cause: le categorie diverse da `codice` puntano a monte;
- **quante escalation, e di che tipo**: escalation ripetute sullo stesso argomento indicano una lacuna dello studio;
- **gli interruttori scattati e la loro causa.**

Ogni lezione diventa una proposta concreta di modifica: alla skill (con `skill-creator`), a un template, a uno script, a un controllo preliminare. Il registro archiviato entra nel banco di prova: è il dato che permette di dire se la versione successiva del metodo è migliore, invece di sperarlo.
