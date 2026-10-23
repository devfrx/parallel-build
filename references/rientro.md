# Rientro

Il rientro è la porta stretta del metodo: ogni ramo passa di qui, uno alla volta, e il branch d'integrazione resta verde dopo ognuno. È la parte seriale, quindi decide la velocità reale della costruzione: va resa rapida (gate incrementali, nessun passaggio manuale superfluo) e inflessibile (nessuna eccezione "solo per questa volta").

## Procedura per un ramo

Dal checkout principale, sul branch d'integrazione pulito. I rami si prendono man mano che i sotto-agenti finiscono; dentro un'ondata non hanno dipendenze reciproche, quindi l'ordine d'arrivo va bene.

1. **Esito.**
   ```bash
   python scripts/valida_esito.py <percorso-esito> --piano .build/piano.toml --task <id>
   ```
   - Esito `bloccato`: è un'escalation (`delega-ed-esito.md`), il ramo aspetta.
   - Esito `parziale`, o validazione fallita: torna al proprietario.
2. **Ownership.**
   ```bash
   python scripts/verifica_ownership.py --piano .build/piano.toml --task <id> \
       --base <branch-integrazione> --ramo <ramo>
   ```
3. **Trailer di co-autore.**
   ```bash
   git log --format=%B <branch-integrazione>..<ramo> | grep -i "co-authored-by"
   ```
   Non deve trovare nulla. Se trova qualcosa, il ramo torna al proprietario per riscrivere i messaggi.
4. **Merge senza commit.**
   ```bash
   git merge --no-ff --no-commit <ramo>
   ```
   Se c'è un conflitto, `git merge --abort` e vedi *Conflitti* più sotto.
5. **Aggiornamenti dell'orchestratore, nello stesso merge.** Per un task di esemplari o di costruzione:
   - togli dall'elenco dei moduli in attesa la voce del suo lato (`backend:<modulo>` o `frontend:<modulo>`);
   - per un backend, porta l'interruttore del modulo da mock a reale.
6. **Gate incrementale**, sul checkout con il merge applicato:
   - i criteri del task, con `{modulo}` risolto;
   - `fitness` e `lint`, che sono rapidi e globali.

   Per un task di **oracoli** il gate è diverso: i test del modulo devono essere rossi per la ragione giusta. Leggi i fallimenti e controlla che siano asserzioni o "non implementato", non errori di sintassi, import o configurazione.
7. **Esito del gate.**
   - **Verde**: `git commit`, con il messaggio nello stile del repo e senza trailer di co-autore. Registra `rientro_ok`.
   - **Rosso**: `git merge --abort`. Il checkout torna allo stato di prima, compresi gli aggiornamenti del passo 5. Registra `rientro_ko` con la causa, poi decidi tra ciclo di correzione e interruttore sistemico.

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
3. **Correggi a monte**, in un task seriale della sessione: contratto, esemplare, generatore, brief, scheletro o ambiente. Una correzione strutturale, come un cambio di contratto, è una decisione dell'utente e passa dalla gestione del cambiamento.
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
2. Le voci dei moduli costruiti non sono più nell'elenco d'attesa.
3. `suite` e CI sono verdi. Se la suite fallisce dove i gate incrementali passavano, ogni merge commit è un punto di ripristino: bisect sui merge dell'ondata.
4. Tag `build/<ondata>`, evento `ondata_fine`.
5. Le escalation non bloccanti vanno all'utente in blocco.
6. I `candidati_promozione` degli esiti si valutano. Quelli accettati si promuovono in un task seriale della sessione: lo spostamento nel codice condiviso e l'aggiornamento dei moduli che lo usano, con i gate. Ora si può, perché nessun task parallelo è in corso.

Un rientro sbagliato si annulla con `git revert -m 1 <merge>`, che non riscrive la storia. Tornare indietro di un'intera fase è una decisione dell'utente.

## Gestione del cambiamento

**Richiesta nuova a costruzione avviata.** Va in `.build/backlog.md` con data e motivo, e il report finale la elenca. Non entra in questa costruzione: lo scope congelato è ciò che rende possibile il parallelismo. Se l'utente la vuole comunque dentro, è un cambio di scope, e si tratta come un cambio di contratto.

**Cambio di contratto** (specifica, facciata, matrice, schema), da un'escalation o dall'utente:

1. **Analisi d'impatto**: quali task leggono il contratto (campo `legge` del piano), quali oracoli lo verificano, quali mock e codici generati ne derivano, quali moduli usano la facciata.
2. **Decisione dell'utente**, con l'impatto davanti.
3. **Applicazione seriale**, nella sessione:
   - aggiorna il contratto e rigenera codice e mock;
   - un `test-author` aggiorna gli oracoli coinvolti, in un task dedicato;
   - i task coinvolti incorporano il cambiamento con il merge del branch d'integrazione nel loro ramo.
4. **Registrazione** dell'evento `cambiamento`. Se la decisione è strutturale, si aggiorna l'ADR.

**Oracolo contestato.** Decide l'utente, con l'argomento del costruttore e il testo della storia davanti. Se l'oracolo è sbagliato, lo corregge un `test-author` in un task dedicato, e si registra un `cambiamento`. Mai il costruttore, mai l'orchestratore dentro un merge.

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
