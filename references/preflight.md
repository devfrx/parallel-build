# Controllo preliminare

La costruzione parallela dipende da comportamenti dell'ambiente che cambiano tra versioni di Claude Code e che, quando sono sbagliati, falliscono in silenzio:

- un worktree che parte dalla base sbagliata produce codice coerente con uno stato vecchio;
- una skill non precaricata produce un costruttore che ignora le convenzioni;
- una regola di deny non attiva lascia installare dipendenze;
- due costruttori che condividono lo stesso database di test si corrompono i dati a vicenda.

Nessuno di questi errori si vede. Per questo il controllo è funzionale dove può: un sotto-agente di prova dimostra il comportamento, invece di leggere una configurazione e presumere.

Annota ogni controllo in `.build/preflight.md` (passato, fallito o non applicabile, con la prova) e registra l'evento `preflight` con `scripts/registro.py`. I fatti su Claude Code citati qui sono quelli di `FONTI.md` di `app-blueprint`, con la data della verifica: se la versione in uso si comporta diversamente, rileggi la documentazione invece di adattare il controllo a memoria.

Il controllo ha due parti: la prima si esegue prima dello scheletro, la seconda dopo, perché alcune cose (comandi reali, regole di deny) esistono solo a scheletro finito. A un incremento successivo al primo si ripetono la Parte 1 e la Parte 2 sullo scheletro esistente: l'ambiente può essere cambiato tra un incremento e l'altro.

## Parte 1 — Prima dello scheletro

### Repository

- Nel checkout principale è attivo il branch d'integrazione del piano.
- Il working tree è pulito (`git status --porcelain` vuoto). I worktree partono dal commit: ciò che non è committato, i sotto-agenti non lo vedono.
- `.build/` e `.claude/worktrees/` sono ignorati. Verificalo con `git check-ignore -v .build/x .claude/worktrees/x`. La documentazione di Claude Code consiglia `.claude/worktrees/` in `.gitignore`; `.build/` va in `.git/info/exclude`.
- **L'incremento è congelato**: `progetto.py verifica --congelamento stato` senza errori. Controlla la Definition of Ready alla data del congelamento, e che il piano sia dell'incremento corrente. Se qualcosa è cambiato dopo il congelamento, una modifica approvata l'ha annullato e lo script lo dice: si ricongela con `app-blueprint` prima di costruire.

### Impostazioni dei worktree

- **`worktree.baseRef: "head"`** nelle impostazioni del progetto. Con il valore predefinito (`"fresh"`) i worktree dei sotto-agenti partono dal branch di default del remoto: non vedrebbero né lo scheletro né gli esemplari, che esistono solo in locale. Il valore non accetta nomi di branch: per questo il branch d'integrazione deve essere quello attivo nel checkout principale.
- **Dipendenze nei worktree.** Un worktree è un checkout nuovo, senza dipendenze installate. Due strade, da scegliere e annotare:
  - **`worktree.symlinkDirectories`** (per esempio `["node_modules", "vendor"]`): collega le cartelle del checkout principale invece di reinstallarle. È veloce, ma la cartella è condivisa da tutti gli agenti, e questo comporta tre cose:
    - le installazioni devono essere vietate, e lo saranno da fine scheletro;
    - la pulizia automatica dei worktree può fallire, perché git rifiuta di rimuovere worktree con file non tracciati, come i collegamenti. In chiusura la pulizia è manuale;
    - strumenti che scrivono cache dentro la cartella condivisa possono collidere: lo verifica la Parte 2.
  - **Installazione dal lockfile in ogni worktree** (`[comandi].installa`, per esempio `npm ci`): più lenta e richiede rete, ma nulla è condiviso. Il costruttore la esegue come primo passo.
- **`.worktreeinclude`** per i file ignorati che servono ai test, come un `.env.testing`. Mai segreti di produzione: ogni worktree ne riceve una copia.

### Permessi

- **Regole di allow** per i comandi del piano (test, lint, typecheck, fitness) e per `git add` e `git commit` nei worktree. I sotto-agenti in background ti chiedono i permessi nella sessione principale: senza queste regole un'ondata si ferma ad aspettare un clic.
- **Regole di deny**, da preparare ora e attivare a fine scheletro:
  - i comandi che aggiungono dipendenze nello stack in uso, per esempio `Bash(npm install *)`, `Bash(composer require *)`, `Bash(pip install *)`;
  - la pubblicazione, `Bash(git push *)`.

  Le installazioni dal lockfile (`npm ci`, `composer install`) restano permesse se servono ai worktree. Le regole di deny nelle impostazioni valgono anche per i sotto-agenti.

### Agenti e skill

- Le cinque definizioni di agente sono disponibili: in `.claude/agents/` del progetto, dove le installa `app-blueprint` alla voce 0.03, in un plugin o in `~/.claude/agents/`.
- **Le skill precaricate si risolvono davvero.** Se una skill elencata nel campo `skills` manca, Claude Code la salta e lo annota solo nel log di debug, quindi un costruttore senza `dev-discipline` lavora comunque, senza che nessuno se ne accorga. La sonda della 0.03 lo verifica; ripetila se le definizioni o l'ambiente sono cambiati da allora: "Senza usare strumenti, per ogni skill precaricata nel tuo contesto riporta il nome e la prima frase dopo il titolo principale". Le skill distribuite in un plugin possono richiedere il nome con il prefisso del plugin.
- **Agent teams.** Verifica se sono attivi. In ogni caso valgono le due regole di lancio di SKILL.md: isolamento passato nella chiamata, nessun nome ai sotto-agenti.

### Prova funzionale del worktree

Lancia un `backend-builder` con l'isolamento passato nella chiamata e questo compito:

1. riporta `pwd`, `git rev-parse HEAD` e `git rev-parse --abbrev-ref HEAD`;
2. esegui `git check-ignore -v .build/esiti/prova.json`;
3. crea un file banale, committalo sul tuo ramo, e scrivi un esito di prova in `.build/esiti/prova.json`;
4. riporta il percorso assoluto dell'esito.

Verifica cinque cose:

- l'HEAD riportato coincide con l'HEAD del branch d'integrazione;
- `.build/` è ignorata anche dentro il worktree;
- il commit esiste sul ramo del worktree;
- l'esito è leggibile dal checkout principale al percorso riportato;
- `git log` sul ramo non contiene trailer di co-autore. Se ne contiene, il brief va rafforzato prima dell'ondata.

Poi **riprendi lo stesso agente** con il suo id e chiedigli `pwd`. Se riporta lo stesso worktree, il ciclo di correzione userà la ripresa. Altrimenti userà il rilancio sul ramo del task, descritto in `delega-ed-esito.md`.

Infine rimuovi il worktree e il ramo di prova. Controlla il nome prima di cancellare il ramo: non è mergiato per costruzione, quindi serve `git branch -D`, e un nome sbagliato cancella lavoro vero.

### Capacità

- **Concorrenza.** Il limite predefinito è di 20 sotto-agenti concorrenti (variabile `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`). Oltre, l'ondata procede a lotti.
- **Limiti d'uso.** I sotto-agenti consumano gli stessi limiti d'uso della sessione: un'ondata da dieci costruttori li consuma circa dieci volte più in fretta. Decidi con l'utente la dimensione dei lotti in base al suo piano d'abbonamento.

## Parte 2 — Dopo lo scheletro

- **Regole di deny attive.** Un sotto-agente banale prova una forma innocua di un comando vietato, per esempio `git push --dry-run`. Deve essere rifiutato.
- **Comandi reali nei worktree.** Un sotto-agente esegue `modulo_backend` e `modulo_frontend` su un modulo dello scheletro dentro il suo worktree. Prova che le dipendenze sono raggiungibili e che i comandi funzionano fuori dal checkout principale.
- **Esecuzioni parallele senza collisioni.** I worktree isolano i file, non i processi. Lancia due sotto-agenti che eseguono insieme gli stessi comandi di test, e se il piano ha test end-to-end anche `e2e`, in due worktree diversi: entrambi devono passare. Se collidono, lo scheletro va corretto prima delle ondate. Le cause tipiche:
  - lo stesso database di test: serve un database per esecuzione, in memoria o con un nome unico;
  - la stessa porta del server: serve una porta libera scelta all'avvio;
  - una cache condivisa: serve una cartella temporanea per esecuzione.
- **Tempo del gate incrementale.** Misura quanto impiegano `modulo_backend`, `modulo_frontend` e `fitness` su un modulo, e annotalo. Il rientro è seriale: N task costano N volte quel tempo. Se il gate supera qualche minuto, ottimizzalo ora, quando costa poco.

## Esito

Tutto passato: registra `preflight` con esito `passato` e procedi. Un controllo fallito: correggi e ripeti, oppure fermati e dillo all'utente con la prova. Non si parte "intanto", sperando che il problema non si presenti: si presenterà durante un'ondata, moltiplicato per il numero di agenti.
