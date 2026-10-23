# Ambienti e scheletro

Le voci 7.09 e 7.10: gli ambienti che il profilo chiede, e un walking skeleton che attraversa tutti gli strati dell'architettura. Lo scheletro è ciò che tutti gli agenti condivideranno: lo costruisce la sessione principale, in serie, perché un errore qui non è un errore, è lo stesso errore in ogni modulo. Si fa dopo la Parte 1 del controllo preliminare (`preflight.md`); con lo scheletro finito si esegue la Parte 2 e si chiude il gate della fase 7.

## 7.09 Ambienti

Quelli di `[[ambienti]]` (`progetto.py mostra ambiente:<id>`), disponibili davvero: locale riproducibile per i servizi (database e simili, documentato nel README), e test, staging o produzione secondo il profilo. La voce vale sempre; con un'esposizione personale o pubblicabile gli ambienti di solito sono il locale e uno di prova. L'evidenza è il comando che avvia ciascun ambiente, o l'URL. Un ambiente che qui non si può avere, come uno staging senza l'infrastruttura, non si esclude: la voce si chiude `--non-verificabile`, con ciò che servirebbe e l'approvazione dell'utente.

## 7.10 Walking skeleton

La sessione lo costruisce sul branch d'integrazione. Ogni voce esiste perché toglie ai costruttori una decisione o un file condiviso.

1. **Progetto e tooling** secondo gli ADR e `ST-qualita-codice`: lint, formatter, typecheck configurati; ogni script nominato in `[comandi]` del piano esiste. `modulo_backend` e `modulo_frontend` accettano l'id del modulo.
2. **Elenco d'attesa** (per esempio `tests/in-attesa.txt`): gli oracoli che possono essere rossi perché il codice non c'è ancora, una riga ciascuno, nella forma con cui il runner li seleziona, cioè per id: `storia:CLI-1` per i test d'accettazione, contratto e autorizzazione che portano l'id della storia (D.12), `percorso:PC-1` per i test end-to-end, `motore:prezzi` per la suite di conformità di un motore. Ci sono le storie dell'incremento, i suoi percorsi critici e i motori che costruisce, nient'altro: gli oracoli degli incrementi precedenti restano nella suite, verdi. `suite` e CI escludono ciò che è in elenco; `modulo_backend` e `modulo_frontend` eseguono sempre i test del modulo, perché sono i comandi con cui il costruttore lavora. Il file è intoccabile per i task: lo aggiorna l'orchestratore al rientro (`rientro.md`).
3. **CI** secondo `ST-ci-cd`, con gli stessi comandi del piano (una sola fonte, nessuna deriva) più i gate della supply chain: audit delle vulnerabilità, licenze, scansione dei segreti, SBOM se il profilo la chiede.
4. **Isolamento dei test in parallelo.** Ogni esecuzione usa un proprio database (in memoria, o con un nome unico), una propria porta per il server dei test end-to-end e proprie cartelle temporanee. I worktree isolano i file, non i processi: senza questa voce due costruttori si corrompono i dati a vicenda e i test diventano rossi a caso.
5. **Migrazioni** da `progetto.py schema`: le tabelle, le colonne e gli indici dell'incremento, e nient'altro. Ciò che lo schema progetta per incrementi futuri non entra in una migrazione ora. Factory e seed con dati sintetici.
6. **Kernel condiviso**, dalle strategie trasversali (`progetto.py mostra ST-<tema>`): autenticazione; applicazione della matrice delle autorizzazioni con negazione per default e condizioni di proprietà; modello degli errori dal catalogo; log e osservabilità; validazione dalle regole del catalogo; configurazione; tempo; audit; tabelle di piattaforma.
7. **Codice generato dalla specifica**: tipi, client del frontend, mock costruito dagli esempi (compresi quelli d'errore), supporto ai test di contratto che validano le risposte contro la specifica.
8. **Interruttore mock/reale** per modulo, in configurazione. Il frontend di un modulo parte sul mock e passa al reale quando il suo backend rientra.
9. **Shell dell'interfaccia** con `frontend-craft`: layout, tabella delle rotte con tutte le schermate dell'incremento come stub, token e componenti del design system, testi dalle chiavi di `ux/testi.toml`.
10. **Registri precompilati.** Rotte, iniezione delle dipendenze, navigazione, permessi: ogni modulo è già registrato con i suoi stub, così nessun costruttore tocca un registro condiviso.
11. **Facciate**: interfaccia e implementazione finta per ogni operazione di facciata del dettaglio dei moduli, così chi dipende da un modulo compila e si testa senza aspettarlo.
12. **Fitness function**: le regole di confine tra moduli (si attraversano solo facciate ed eventi), eseguite in CI.
13. **Generatori** per archetipo: creano i file di un modulo nuovo. Ora sono abbozzi; diventano definitivi dagli esemplari.
14. **`CLAUDE.md` snello**, con `lean-docs`: comandi, struttura, convenzioni e regole per gli agenti (ownership, oracoli intoccabili, escalation, nessun trailer di co-autore), più i rimandi alle schede degli esemplari. Un sotto-agente in worktree non lo legge dal suo worktree: carica le istruzioni che la conversazione principale aveva all'avvio (`FONTI.md` di `app-blueprint`), che possono essere di prima dello scheletro. Per questo la parte comune del brief incolla il `CLAUDE.md` corrente. Ogni riga si paga una volta per agente.
15. **README**: come si avvia, come si testa.

Il walking skeleton attraversa tutti gli strati: almeno una richiesta va dall'interfaccia al database e torna, passando per kernel, autorizzazioni ed errori, anche se ogni modulo risponde "non implementato".

### Chiusura

1. Esegui ogni comando del piano: tutti verdi sullo scheletro vuoto. Se un test runner fallisce quando non trova test, configuralo perché non lo faccia: è un errore che arriverebbe alle ondate travestito da fallimento del costruttore.
2. Committa e applica il tag `build/incremento-<n>/scheletro`.
3. Attiva le regole di deny delle installazioni ed esegui la Parte 2 del controllo preliminare.
4. Chiudi 7.09 e 7.10 con le evidenze: i comandi degli ambienti, il tag, l'esito della Parte 2.

Lo schema realizzato e i container descrivono ora ciò che esiste: le viste di `docs/progettazione/viste/` li mostrano già, e se il codice diverge dal progetto è una modifica, non un aggiornamento dei diagrammi.

## Gate della fase 7

Il congelamento ha chiuso la parte di `app-blueprint`; questo gate dice che il progetto congelato gira. Il brief: ambienti disponibili, scheletro e tag, comandi verdi, esito del controllo preliminare con i tempi del gate incrementale e la concorrenza decisa. Con l'approvazione dell'utente, `progetto.py approva 7 --da <chi approva>`.

## Incrementi successivi

Lo scheletro esiste già: la 7.09 resta chiusa, la 7.10 si richiude a ogni incremento. Prima degli oracoli, la sessione lo estende in serie per ciò che l'incremento aggiunge: migrazioni da `progetto.py schema --nuovi`, compatibili all'indietro secondo `ST-migrazioni`, comprese quelle delle modifiche che `schema --nuovi` elenca; stub, registrazioni e facciate finte dei moduli e delle operazioni nuovi; codice e mock rigenerati dalla specifica; nell'elenco d'attesa le storie, i percorsi e i motori del nuovo incremento. Ciò che un cambio tocca in elementi già costruiti arriva da una modifica approvata, con il suo impatto, e dal diff delle sorgenti rispetto al tag del congelamento precedente. Tag `build/incremento-<n>/scheletro`, e la 7.10 si chiude con quello.
