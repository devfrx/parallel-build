# Integrazione, verifica, accettazione, rilascio

Le fasi 9–12 di ogni incremento. Dimostrano ciò che si può dimostrare e dichiarano il resto; nessuna aggiunge funzionalità. Le voci che valgono le dice il profilo (`progetto.py checklist --fase N`): un progetto pubblicabile ne rinvia molte al debito di pubblicazione. Ogni voce si chiude con un'evidenza. Una voce che serve ma che in questo ambiente non si può verificare non è un'esclusione: si chiude `--non-verificabile`, con il motivo "serve <cosa>" e l'approvazione dell'utente, e il report la elenca tra il non verificato. Una voce che al progetto non serve si esclude come sempre, con il motivo. Queste quattro fasi sono la production readiness review del metodo.

Indice: Integrazione (9) · Verifica (10) · Validazione e accettazione (11) · Rilascio (12) · Report di consegna · Pulizia · Retrospettiva · Fine dell'incremento.

## Fase 9 — Integrazione

- **9.01** La strategia d'integrazione è quella del metodo, continua: ogni ramo rientra da solo, con i gate, e nessun big bang. L'evidenza è il registro di build.
- **9.02** Test d'integrazione con dipendenze reali o containerizzate (database, posta di prova, code) verdi.
- **9.03** Test di contratto tra moduli e verso l'API verdi: gli oracoli di contratto e i test delle facciate, ora contro le implementazioni vere invece degli stub.
- **9.04** Con l'innesco `integrazioni`: ogni integrazione provata nel suo ambiente di prova, comprese le risposte d'errore, i timeout e i tentativi della sua voce in `[[integrazioni]]`.
- **9.05** Le differenze tra ambienti vivono solo in configurazione, secondo `contracts/configurazione.toml`.
- **9.06** Con l'innesco `migrazione-dati`: migrazione provata su una copia realistica, con verifica d'integrità e riconciliazione dei conteggi.
- **9.07** Installazione e avvio da un checkout pulito, seguendo il README, in un ambiente simile alla produzione.
- **9.08** I percorsi critici end-to-end verdi sull'app integrata. I test li hanno scritti i task end-to-end dell'ondata degli oracoli; ora le righe `percorso:` escono dall'elenco d'attesa, nello stesso commit che li vede verdi. Qui un test rosso non è atteso: è un difetto, e torna al proprietario del modulo attraverso il rientro. L'autore del test non corregge l'app. Tag `build/incremento-<n>/e2e`.

## Fase 10 — Verifica

### 10.01 Revisione per lenti

Tre `reviewer` in parallelo sull'app integrata, ciascuno con una lente, in sola lettura: possono eseguire comandi per raccogliere prove, non modificare file.

- **Sicurezza.** La matrice delle autorizzazioni contro il codice: ogni regola applicata nel backend, nessuna operazione che sfugge al kernel, le condizioni di proprietà valide anche per gli id passati nell'URL o nel corpo. Validazione degli input ai confini di fiducia; segreti e dati personali nel codice o nei log; i gate di supply chain; le minacce del threat model, ciascuna con la sua contromisura; i requisiti ASVS dei moduli. Per i moduli ad alto rischio la lente è obbligatoria e va letta riga per riga, e l'utente guarda il diff.
- **Coerenza.** Aderenza agli esemplari e alle convenzioni, gestione degli errori uniforme, duplicazione tra moduli (candidati alla promozione mancati), confini che le fitness function non vedono, prestazioni del backend: query ripetute per ogni elemento, query senza indice sui percorsi critici, elenchi senza limite.
- **Interfaccia.** Con il metodo di revisione di `frontend-craft`: gerarchia, stati, accessibilità al livello del profilo, prestazioni, aderenza ai mockup, ai token e ai testi.

Un finding per riga, `percorso/file.ext:riga [P1] cosa non va — prova`, con questa scala: **P0** blocca una storia dell'incremento, espone dati o denaro, o causa perdita di dati; **P1** viola un contratto, la matrice, un requisito misurato o il livello d'accessibilità; **P2** è un fastidio o un costo di manutenzione con una via d'uscita; **P3** rifinitura. Un finding senza prova è un'ipotesi, marcata come dedotta.

L'orchestratore deduplica, verifica i P0 e i P1 riproducendo la prova, assegna ogni correzione al proprietario del percorso secondo il piano (ripresa o rilancio, come nel ciclo di correzione) e la fa rientrare con la procedura normale. Un finding che chiede di cambiare un contratto o un oracolo è una modifica. P0 e P1 si chiudono, o l'utente li accetta come rischio, con il motivo nel report; P2 e P3 vanno nel debito o tra le modifiche proposte. Tag `build/incremento-<n>/revisione`.

### Le altre verifiche

- **10.02** Analisi statica completa, senza problemi bloccanti.
- **10.03** Con criticità regolamentata, metodi formali sulle parti critiche, dove la norma li prevede.
- **10.04** Casi di test progettati con tecniche sistematiche: quelle dichiarate in `piano/test.toml` per l'accettazione, applicate dagli oracoli.
- **10.05** Test di sistema ed end-to-end sui flussi prioritari verdi.
- **10.06** Regressione automatizzata verde: `suite` in CI.
- **10.07** Prestazioni contro gli scenari degli RNF, con la prova che ciascuno dichiara: carico, stress, durata, picchi.
- **10.08** Sicurezza verificata con SAST, DAST e analisi delle dipendenze; fuzzing e penetration test dove il livello ASVS o il profilo li prevedono.
- **10.09** Failover e ripristino da backup provati davvero, contro RPO e RTO.
- **10.10** Compatibilità con browser e dispositivi del design system, accessibilità (controlli automatici più la lente interfaccia), installazione e aggiornamento, migrazioni comprese.
- **10.11** Efficacia dei test oltre la copertura: mutation testing sulle parti critiche, come i criteri dei moduli ad alto rischio.
- **10.12** Difetti residui non bloccanti elencati e accettati dall'utente: ciascuno in `[[debito]]` o in `[[rischi]]` di `registri.toml`, con l'accettazione; il report li elenca.
- **10.13** Cause radice dei difetti ricorrenti, dal registro di build: le cause di categoria diversa da `codice` puntano a monte, e diventano modifiche o lezioni.

## Fase 11 — Validazione e accettazione

- **11.01** Test d'accettazione utente: l'utente percorre le storie dell'incremento nell'ambiente di prova, sui criteri della fase 2. L'esito è una revisione di tipo `accettazione` in `registri.toml`, con i difetti trovati.
- **11.02** Con esposizione pubblica: accettazione operativa da chi gestirà il sistema (backup, monitoraggio, ripristino, runbook), revisione di tipo `operativa`.
- **11.03** Con esposizione pubblica: alfa, beta o pilota con utenti reali, feedback gestito.
- **11.04** Conformità verificata secondo gli inneschi: privacy, accessibilità, sicurezza, contratti, norme di settore. Con `compliance-docs`, e con i documenti da far rivedere a un professionista prima del lancio.
- **11.05** Valutazione di conformità o certificazione, dove la norma la richiede.
- **11.06** Tracciabilità chiusa: ogni storia dell'incremento e ogni RNF verificabile ha almeno un test e un esito. La catena storia → oracoli ed end-to-end è in `viste/tracciabilita.md`, che è generata e non si tocca; gli esiti li dà il rapporto della suite, attraverso gli id delle storie nei nomi dei test, ed è l'evidenza della voce insieme alla vista.
- **11.07** Ogni obiettivo misurabile della fase 1 ha un modo di essere misurato in esercizio: la sua `misura` è implementata o pianificata.
- **11.08** Verbale di accettazione: l'utente accetta l'incremento, esplicitamente. È la revisione d'accettazione con esito positivo, e la sua approvazione chiude anche la fase.

## Fase 12 — Rilascio e transizione in esercizio

Il rilascio segue il `rilascio` dell'incremento nel piano: locale, staging o produzione.

- **12.11** Sempre: README e runbook coprono avvio, test, deploy, rollback e ripristino da backup, e dicono dove guardare quando qualcosa va storto (le convenzioni d'osservabilità). `CLAUDE.md` passa dalle regole della costruzione a quelle del lavoro ordinario, snello con `lean-docs`.
- **12.01–12.10**, con esposizione pubblica e secondo gli inneschi: pipeline di rilascio con artefatti immutabili e firmati e provenienza verificabile; strategia di rilascio con criteri di arresto; rollback provato, migrazioni comprese; migrazione dei dati e cut-over; monitoraggio e allarmi attivi prima del go-live; runbook, reperibilità ed escalation; utenti e supporto formati, documentazione utente; note di rilascio; hypercare con i responsabili, e a fine hypercare metriche stabili senza incidenti bloccanti. Con un progetto pubblicabile sono il debito di pubblicazione.

## Report di consegna

`docs/consegna/incremento-<n>/report.md` con `assets/report-consegna.md`, alla fine della fase 12, committato: resta con il progetto, mentre un `.build/` svuotato alla pulizia lo perderebbe. Separa ciò che è verificato (eseguito, con prova), ciò che è dedotto e ciò che non è verificato; riporta le escalation aperte, le modifiche proposte, i rischi accettati, le voci rinviate e le metriche del registro (`scripts/registro.py riepilogo`). Un report che sembra più completo di quanto sia è debito che matura sul primo che costruisce sopra. All'utente si consegna con in testa ciò che deve sapere subito.

## Pulizia

- **Worktree dei task**: per ognuno, `git status` per verificare che non contenga lavoro non rientrato, poi `git worktree remove`. Con le cartelle collegate (`symlinkDirectories`) git rifiuta senza `--force`: usalo solo dopo il controllo.
- **Rami dei task**: `git branch -d`, che rifiuta i rami non mergiati. Un rifiuto è un'informazione, non un ostacolo da forzare. I rami delle prove a secco, non mergiati per costruzione, si cancellano con `-D`, controllando il nome uno per uno.
- **Regole di deny temporanee**: si tolgono, se l'utente non vuole tenerle.
- **`.build/`**: il registro di build si archivia fuori dal repo, dove dice l'utente, perché serve alla retrospettiva e al confronto tra versioni del metodo; poi la cartella si svuota. Nessuna evidenza vive qui: brief degli esemplari e report stanno in `docs/consegna/`.

## Retrospettiva

Dal registro, non dalla memoria: dove è andato il tempo (rientro contro sotto-agenti), quante volte un task è tornato indietro e per quali cause, quante escalation e su cosa, gli interruttori scattati. Le categorie diverse da `codice` puntano a monte: al progetto, agli esemplari, ai brief. Ogni lezione diventa una proposta concreta: una modifica al progetto, o una modifica alla skill, a un template, a uno script, a un controllo preliminare.

## Fine dell'incremento

Con la fase 12 approvata, l'incremento è chiuso. Il successivo lo apre `app-blueprint` con `progetto.py incrementa`, che lo controlla, e le modifiche proposte durante la costruzione si decidono lì, per prime.
