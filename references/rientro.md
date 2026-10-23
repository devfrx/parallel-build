# Rientro

Il rientro è la porta stretta del metodo: ogni ramo passa di qui, uno alla volta, e il branch d'integrazione resta verde dopo ognuno. È la parte seriale, quindi decide la velocità reale della costruzione: va resa rapida (gate incrementali, nessun passaggio manuale superfluo) e inflessibile (nessuna eccezione "solo per questa volta").

Indice: Procedura per un ramo · Le cause, scritte per essere contate · Interruttore sistemico · Conflitti · Fine ondata · Gestione del cambiamento · Eventi del registro.

## Procedura per un ramo

Dal checkout principale, sul branch d'integrazione pulito. I rami si prendono man mano che i sotto-agenti finiscono; dentro un'ondata non hanno dipendenze reciproche, quindi l'ordine d'arrivo va bene.

1. **Esito.**
   ```bash
   python scripts/valida_esito.py <percorso-esito> --piano docs/progettazione/piano/piano.toml --task <id>
   ```
   - Esito `bloccato`: è un'escalation (`delega-ed-esito.md`), il ramo aspetta.
   - Esito `parziale`, o validazione fallita: torna al proprietario.
2. **Ownership.**
   ```bash
   python scripts/verifica_ownership.py --task <id> --base <branch-integrazione> --ramo <ramo>
   ```

   Il piano si legge da `docs/progettazione/piano/piano.toml`; `--piano` cambia il percorso.
3. **Trailer di co-autore e push.**
   ```bash
   git log --format=%B <branch-integrazione>..<ramo> | grep -i "co-authored-by"
   git ls-remote --heads origin <ramo>
   ```
   Nessuno dei due deve trovare nulla. Un trailer: il ramo torna al proprietario per riscrivere i messaggi. Un ramo sul remoto: un sotto-agente ha pubblicato, è un'escalation all'utente.
4. **Merge senza commit.**
   ```bash
   git merge --no-ff --no-commit <ramo>
   ```
   Se c'è un conflitto, `git merge --abort` e vedi *Conflitti* più sotto.
5. **Aggiornamenti dell'orchestratore, nello stesso merge.** Per un task di motore, esemplari o costruzione:
   - togli dall'elenco d'attesa le storie dell'incremento i cui moduli, quello che le orchestra e quelli che toccano, sono ora tutti rientrati per tutti i lati che hanno nel piano; per un motore, la sua riga `motore:`; i percorsi critici escono alla 9.08;
   - per un backend, porta l'interruttore del modulo da mock a reale;
   - `git add` di ciò che hai cambiato, così il gate lo prova e il passo 7 lo committa o lo annulla insieme al merge.
6. **Gate incrementale**, sul checkout con il merge applicato:
   - i criteri del task, con `{modulo}` risolto;
   - `fitness` e `lint`, che sono rapidi e globali.

   Per un task di **oracoli**, anche end-to-end, il gate è diverso: i criteri del task (di solito `lint`) passano, e i test nuovi sono rossi per la ragione giusta, come l'esito li dichiara (`rosso-atteso`). Esegui il comando del modulo, o `e2e`, e leggi i fallimenti: asserzioni, "non implementato", elementi che lo stub non mostra; non errori di sintassi, import o configurazione. La suite resta verde, perché ciò che è rosso è in elenco d'attesa.

   Il gate incrementale è anche la DoD di livello `task`, per ciò che un comando vede: i criteri del task (D.01, D.03), lint e fitness (D.02), l'ownership che lascia intatti contratti e oracoli (D.10), lo scanner dei segreti se è rapido (D.07). L'esito dice cosa cambia nella documentazione (D.11) e cosa resta indietro: ciò che è debito va in `[[debito]]` (D.13). Ciò che un comando non vede, come log senza dati personali (D.08), lo guardano le lenti della revisione.
7. **Esito del gate.**
   - **Verde**: `git commit`, con il messaggio nello stile del repo e senza trailer di co-autore. Registra `rientro_ok`.
   - **Rosso**: `git merge --abort`. Il checkout torna allo stato di prima, compresi gli aggiornamenti del passo 5, che sono nell'indice. Registra `rientro_ko` con la causa, poi decidi tra ciclo di correzione e interruttore sistemico.

Il worktree di un task si rimuove solo a task chiuso: una ripresa ci lavora ancora dentro.

## Le cause, scritte per essere contate

L'interruttore sistemico funziona solo se due fallimenti con la stessa causa si riconoscono come tali. Scrivi la causa di ogni `rientro_ko` nella forma `categoria: dettaglio`, con la categoria presa da questo elenco:

| Categoria | Esempio di dettaglio |
|---|---|
| `contratto` | `formato degli errori di validazione` |
| `oracolo` | `test FAT-1 si aspetta un campo assente dalla specifica` |
| `esemplare` | `paginazione copiata senza limite massimo` |
| `brief` | `comando dei criteri senza id del modulo` |
| `ownership` | `composer.lock` |
| `ambiente` | `database di test condiviso` |
| `codice` | `errore locale del task` |

Solo `codice` è un fallimento del costruttore. Ogni altra categoria punta a monte.

## Interruttore sistemico

**Quando scatta**: la stessa causa (stessa categoria, stesso dettaglio) fa fallire due o più task della stessa ondata. Oppure un fallimento ha una categoria diversa da `codice` che, per sua natura, tocca tutti i task: un esemplare sbagliato, un comando rotto, un ambiente che collide.

**Cosa fai**:

1. **Fermi l'ondata.** Nessun nuovo lancio e nessun nuovo rientro. Gli agenti già al lavoro finiscono, e i loro rami aspettano.
2. **Registri l'evento** `interruttore`, con la causa.
3. **Correggi a monte**, nella sessione, in serie, direttamente sul branch d'integrazione: esemplare, generatore, brief, scheletro o ambiente. Non è un task del piano, quindi niente esito né `verifica_ownership.py`: la correzione tocca proprio ciò che nessun task possiede. Al suo posto, i gate completi (`suite`, `fitness`, `lint`) e un commit `monte: <categoria>: <dettaglio>`. Una correzione di ciò che è congelato — un contratto, un oracolo — è una modifica, e passa dalla gestione del cambiamento.
4. **Riapri l'ondata.** I rami in attesa e i task da correggere incorporano la correzione portando nel proprio ramo il branch d'integrazione (`git merge <branch-integrazione>`, nel loro worktree). Con l'ownership disgiunta non ci sono conflitti, e questi tentativi non contano nel limite di due.

Correggere a valle, task per task, ciò che ha una causa a monte produce N correzioni diverse dello stesso problema: dieci moduli coerenti con l'esemplare e incoerenti tra loro.

## Conflitti

Se ogni ramo tocca solo i suoi percorsi, e `verifica_ownership.py` lo ha verificato, un conflitto è impossibile. A meno che qualcosa sul branch d'integrazione abbia toccato i percorsi del task dopo che il task è partito: una promozione, una correzione a monte, un file generato da uno strumento.

Un conflitto è quindi sempre un accoppiamento che il piano non ha visto. Non si risolve a mano dentro il rientro:

1. annulla il merge;
2. trova il file e il commit che l'ha toccato;
3. decidi se è un errore del piano (un file condiviso da rendere intoccabile o generato), un file che non doveva essere versionato, o una correzione a monte da far incorporare al ramo;
4. correggi, poi fai rientrare il ramo.

## Fine ondata

1. Tutti i task dell'ondata sono rientrati, oppure sono escalation con una decisione dell'utente su come procedere.
2. Le storie dei moduli rientrati, e i motori, non sono più nell'elenco d'attesa.
3. `suite` e CI sono verdi. Se la suite fallisce dove i gate incrementali passavano, ogni merge commit è un punto di ripristino: bisect sui merge dell'ondata.
4. Tag `build/incremento-<n>/<ondata>`, evento `ondata_fine`.
5. Le escalation non bloccanti vanno all'utente in blocco.
6. I `candidati_promozione` degli esiti si valutano. Quelli accettati li promuove la sessione, in serie, come una correzione a monte: lo spostamento nel codice condiviso e l'aggiornamento dei moduli che lo usano, con i gate completi. Ora si può, perché nessun task parallelo è in corso.

Un rientro sbagliato si annulla con `git revert -m 1 <merge>`, che non riscrive la storia. Tornare indietro di un'intera fase è una decisione dell'utente.

## Gestione del cambiamento

Ciò che è congelato cambia solo con una modifica di `app-blueprint` (`MOD-n` in `registri.toml`), perché il progetto congelato è ciò che rende possibile il parallelismo.

**Richiesta nuova a costruzione avviata.** Si registra come modifica con `esito = "proposta"`, e si valuta all'apertura dell'incremento successivo; il report la elenca. Se l'utente la vuole comunque in questo incremento, è un cambio di scope, e segue la strada del cambio di contratto.

**Cambio di contratto, di oracolo o di scope**, da un'escalation o dall'utente:

1. **Impatto**: `progetto.py impatto <id> [<id>…] --profondita 3` con gli elementi toccati (operazioni, tabelle, facciate, regole della matrice, storie): stampa ciò che ne dipende e le righe `impatto` e `riapre` della modifica. Si aggiungono gli oracoli che li verificano e il codice e i mock che ne derivano.
2. **Decisione dell'utente**, con l'impatto davanti, sulla modifica proposta: ciò che cambia, le voci da riaprire, i task coinvolti.
3. **Applicazione**: con il sì, `progetto.py modifica MOD-n --da <chi approva>`. Annulla le chiusure delle voci riaperte e il congelamento: i task coinvolti si fermano, gli altri possono finire ma non si lancia nulla di nuovo. La sessione lavora le voci riaperte con il protocollo di `app-blueprint`, aggiorna le sorgenti e ricongela con `progetto.py congela`, con revisioni nuove almeno sull'impatto e un nuovo tag.
4. **Propagazione**, in serie: la sessione rigenera codice e mock; gli oracoli coinvolti li aggiorna un `test-author` rilanciando il task di oracoli del loro modulo, lo stesso del piano, con la modifica nel brief: stessi percorsi, quindi stessa ownership; i task coinvolti incorporano il cambio portando nel proprio ramo il branch d'integrazione.
5. **Registro**: evento `cambiamento` con l'id della modifica.

**Oracolo contestato.** Decide l'utente, con l'argomento del costruttore e il testo della storia davanti. Se l'oracolo è sbagliato, è una modifica come sopra, e lo corregge un `test-author` rilanciando il task di oracoli del modulo: mai il costruttore, mai l'orchestratore dentro un merge.

## Eventi del registro, in sintesi

| Momento | Evento |
|---|---|
| lancio, ripresa o rilancio di un task | `delega` (con `--tentativo` e l'id dell'agente in `--nota`) |
| ramo integrato | `rientro_ok` |
| ramo respinto | `rientro_ko` con `--causa "categoria: dettaglio"` |
| domanda dal sotto-agente | `escalation` (con `--bloccante` se lo è) |
| stop dell'ondata | `interruttore` con la causa |
| decisione dell'utente | `decisione` |
| cambio di contratto, scope o oracolo | `cambiamento` |
| inizio e fine di ogni ondata | `ondata_inizio`, `ondata_fine` |
| gate superato o fallito | `gate` |
