# Ondata zero: scheletro, spike, oracoli, esemplari

Il giorno 2 costruisce ciò che tutti gli agenti del giorno 3 condivideranno. È lavoro in gran parte seriale e della sessione principale, con due eccezioni parallele (spike e oracoli), perché un errore qui non è un errore: è lo stesso errore in ogni modulo.

## Scheletro

La sessione principale lo costruisce sul branch d'integrazione. Ogni voce esiste perché toglie ai costruttori una decisione o un file condiviso.

1. **Progetto e tooling** secondo gli ADR: lint, formatter, typecheck configurati; ogni script nominato in `[comandi]` esiste. `modulo_backend` e `modulo_frontend` accettano l'id del modulo.
2. **Elenco dei moduli in attesa** (per esempio `tests/in-attesa.txt`): una voce per lato per ogni modulo, nella forma `backend:veicoli` e `frontend:veicoli`. `suite` e CI escludono gli oracoli delle voci presenti; `modulo_backend` e `modulo_frontend` li eseguono sempre, perché sono i comandi con cui il costruttore lavora sul suo modulo. Il file è intoccabile per i task: lo aggiorna l'orchestratore al rientro.
3. **CI** che esegue gli stessi comandi del piano (una sola fonte, nessuna deriva) più i gate della politica di supply chain: audit delle vulnerabilità, licenze, SBOM, scansione dei segreti.
4. **Ambiente locale** riproducibile per i servizi (database e simili), documentato nel README.
5. **Isolamento dei test in parallelo.** Ogni esecuzione dei test usa un proprio database (in memoria, o con un nome unico per esecuzione), una propria porta per il server dei test end-to-end e proprie cartelle temporanee. I worktree isolano i file, non i processi: senza questa voce due costruttori si corrompono i dati a vicenda e i test diventano rossi a caso.
6. **Migrazioni**, tutte, dall'ER: lo schema è un contratto. Factory e seed con dati sintetici.
7. **Kernel condiviso**:
   - autenticazione;
   - applicazione delle autorizzazioni lette dalla matrice, con negazione per default;
   - modello degli errori;
   - convenzioni di log e osservabilità;
   - validazione e configurazione.
8. **Codice generato dalla specifica**: tipi, client del frontend, mock costruito dagli esempi (compresi quelli d'errore), supporto ai test di contratto che validano le risposte contro la specifica.
9. **Interruttore mock/reale** per modulo, in configurazione. Il frontend di un modulo parte sul mock e passa al reale quando il suo backend rientra.
10. **Shell dell'interfaccia** con `frontend-craft`: layout, tabella delle rotte con tutte le pagine come stub, token, componenti base dall'inventario.
11. **Registri precompilati.** Rotte, iniezione delle dipendenze, navigazione, permessi: ogni modulo è già registrato con i suoi stub, così nessun costruttore tocca un registro condiviso.
12. **Facciate**: interfaccia e implementazione stub per ogni modulo, così chi dipende da un modulo compila e si testa senza aspettarlo.
13. **Fitness function**: le regole di confine tra moduli (si attraversano solo facciate ed eventi), eseguite in CI.
14. **Generatori** per archetipo: creano i file di un modulo nuovo. Ora sono abbozzi; diventano definitivi dagli esemplari.
15. **`CLAUDE.md` snello**, con `lean-docs`: comandi, struttura, convenzioni e regole per gli agenti (ownership, oracoli intoccabili, escalation, commit senza trailer di co-autore), più i rimandi alle schede degli esemplari. Ogni sotto-agente lo carica: ogni riga si paga una volta per agente.
16. **README**: come si avvia, come si testa.

### Chiusura dello scheletro

1. Esegui ogni comando del piano. Tutti verdi sullo scheletro vuoto: i comandi esistono e funzionano. Se un test runner fallisce quando non trova test, configuralo perché non lo faccia: è un errore che arriverebbe al giorno 3 travestito da fallimento del costruttore.
2. Con `design-docs`, sposta dagli ADR a `docs/design/` i diagrammi di ciò che ora esiste, come lo schema realizzato dalle migrazioni e i container.
3. Committa e applica il tag `build/scheletro`.
4. Attiva le regole di deny ed esegui la Parte 2 del controllo preliminare.

## Spike

Per ogni `[[spike]]` del piano, un costruttore del lato pertinente lavora in un worktree, con un brief che dice:

- che è uno spike;
- che il codice è usa e getta e non rientrerà;
- qual è la domanda e quale criterio misura la risposta.

Gli spike girano in parallelo allo scheletro: non ne hanno bisogno.

L'esito è una risposta con la prova, non un ramo da integrare. Se l'assunzione regge, si annota nel registro. Se cade, ci si ferma:

1. con l'utente si aggiorna l'ADR (il vecchio diventa `Superseded`);
2. si correggono contratti e piano, e si rivalida il piano;
3. solo dopo si passa agli oracoli.

Scrivere test su un contratto che sappiamo sbagliato significa scriverli due volte.

I rami degli spike si cancellano a fine giornata.

## Oracoli

Un `test-author` per ogni task `oracoli` del piano, in parallelo, con il brief di `assets/brief-costruttore.md` nella variante per gli oracoli. Scrivono, per il loro modulo:

- **Accettazione**: un test per ogni criterio delle storie, con l'id della storia nel nome o in un'annotazione. È ciò che permette di ricavare la matrice di tracciabilità dai risultati dei test.
- **Contratto**: per ogni operazione del modulo, le risposte validate contro la specifica, compresi i casi d'errore e la paginazione.
- **Autorizzazione**: dalla matrice, chi è consentito passa e chi non lo è riceve l'errore previsto. Per ogni condizione di proprietà, il tentativo sulla risorsa di un altro.
- **Budget**: le liste rispettano la dimensione di pagina e, se lo stack lo permette, un numero massimo di query. Così il problema delle query ripetute per ogni elemento lo trova un test e non un utente.
- **Interfaccia**: componenti e pagine cercati per ruolo e nome accessibile, come fissati nei mockup; gli stati di caricamento, vuoto ed errore, dagli esempi del mock.
- **Moduli ad alto rischio**: test basati su proprietà dove esiste un invariante da esprimere.

**Rosso per la ragione giusta.** Ogni oracolo deve fallire perché il comportamento manca: un'asserzione falsa, una risposta "non implementato" dallo stub. Non deve fallire per un errore di sintassi, di import o di configurazione. Un test che fallisce per la ragione sbagliata diventerà verde per la ragione sbagliata, o non lo diventerà mai.

L'autore lo dichiara nel suo esito. Al rientro l'orchestratore riesegue `modulo_backend` e `modulo_frontend` del modulo e legge i fallimenti, uno per tipo.

Il rientro segue `rientro.md`. Tag `build/oracoli`.

## Esemplari

Per ogni archetipo, la sessione principale costruisce l'esemplare, backend e frontend, contro i suoi oracoli, fino al verde su tutti i criteri del task. Lavora su un ramo dedicato e lo fa rientrare con la stessa procedura di tutti: le regole valgono anche per chi le applica.

L'esemplare verrà copiato, difetti compresi. Quindi deve essere esemplare davvero:

- idiomatico per lo stack;
- con la gestione degli errori del kernel;
- con i test della propria logica, oltre agli oracoli;
- con tutti gli stati dell'interfaccia;
- senza scorciatoie "tanto è il primo".

Poi:

1. aggiorna il generatore dell'archetipo, così i costruttori partono da codice generato già vicino all'esemplare;
2. scrivi in `CLAUDE.md` la **scheda dell'esemplare**: cinque-dieci righe che dicono quali file guardare per quale aspetto, senza ripetere il codice;
3. togli le voci dell'esemplare dall'elenco dei moduli in attesa, nello stesso commit del rientro.

Tag `build/esemplari`.

## Prova a secco

Un costruttore nuovo, del lato più rischioso, riceve un brief per un modulo usa e getta di un archetipo, per esempio una risorsa banale "prova". Ha a disposizione solo `CLAUDE.md`, l'esemplare e il generatore, nessuna spiegazione in più. Osserva:

- ha usato il generatore?
- ha seguito i pattern dell'esemplare, o ne ha inventati?
- ha rispettato l'ownership?
- ha scritto un esito valido?
- dove la documentazione era ambigua, ha fatto un'escalation o ha tirato a indovinare?

Ogni deviazione è un difetto della documentazione, del generatore o del brief, non del costruttore: correggilo ora. Se le correzioni sono state sostanziali, ripeti la prova una volta. Il ramo non rientra, e si cancella.

È il test di manutenibilità anticipato: se un agente nuovo non riesce ad aggiungere un modulo da solo, domani dieci agenti sbaglieranno nello stesso modo.

## Gate eseguibile

Sul branch d'integrazione: ogni comando del piano verde, CI verde. In elenco d'attesa restano solo le voci dei moduli del giorno 3. Registra il gate.

## Gate 2

Scrivi `.build/gate-2.md` con `assets/brief-gate-2.md` e portalo all'utente. Si approvano gli esemplari, cioè i pattern che verranno replicati dieci volte, e un campione degli oracoli, cioè la definizione di "fatto". È l'ultimo momento in cui un cambio di direzione costa un esemplare e non dieci moduli.

Con l'approvazione: tag `build/gate-2`, evento `gate` nel registro, `session-handoff` per la notte.
