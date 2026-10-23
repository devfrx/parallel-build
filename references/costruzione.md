# Implementazione

La fase 8, nelle ondate fisse del piano: oracoli, motore, esemplari, costruzione. Il gate: ogni task del perimetro ha superato la DoD e i controlli sull'intera base di codice sono verdi. Il lancio dei sotto-agenti è in `delega-ed-esito.md`, il rientro di ogni ramo in `rientro.md`.

Indice: Oracoli (8.11) · Motore · Esemplari e prova a secco (8.12) · Ondata di costruzione · Elenco d'attesa (8.13) · Controlli sull'intera base (8.02–8.10) · DoD e gate (8.01).

## Oracoli (8.11)

Un `test-author` per ogni task `oracoli` del piano, in parallelo, compresi i task end-to-end dei percorsi critici. Scrivono, per il loro modulo:

- **Accettazione**: un test per ogni criterio delle storie dell'incremento, con l'id della storia nel nome o in un'annotazione, progettato con le tecniche della strategia di test (`progetto.py mostra livello:accettazione`). È ciò che permette di ricavare la tracciabilità dai risultati dei test.
- **Contratto**: per ogni operazione del modulo, le risposte validate contro la specifica, compresi i casi d'errore e la paginazione.
- **Autorizzazione**: dalla matrice, chi è consentito passa e chi non lo è riceve l'errore previsto. Per ogni condizione di proprietà, il tentativo sulla risorsa di un altro.
- **Budget**: le liste rispettano la dimensione di pagina e, se lo stack lo permette, un numero massimo di query. Così il problema delle query ripetute per ogni elemento lo trova un test e non un utente.
- **Interfaccia**: elementi cercati per ruolo e nome accessibile, come fissati nelle schermate; gli stati di caricamento, vuoto ed errore, dagli esempi del mock.
- **Moduli ad alto rischio**: test basati su proprietà dove esiste un invariante da esprimere, cioè le regole e gli invarianti del modulo.
- **Motore**: la suite di conformità del suo contratto, con test basati su proprietà per gli invarianti.
- **End-to-end**: i percorsi critici, sui nomi accessibili, con tutte le storie dell'incremento che attraversano.

**Rosso per la ragione giusta.** Ogni oracolo deve fallire perché il comportamento manca: un'asserzione falsa, una risposta "non implementato" dallo stub. Non per un errore di sintassi, di import o di configurazione: un test che fallisce per la ragione sbagliata diventerà verde per la ragione sbagliata, o non lo diventerà mai. L'autore lo dichiara nel suo esito; al rientro l'orchestratore riesegue i comandi del modulo e legge i fallimenti, uno per tipo.

Rientro come in `rientro.md`. Tag `build/incremento-<n>/oracoli`; la voce 8.11 si chiude con il tag.

## Motore

Se il piano ne dichiara uno, la sessione lo costruisce nell'ondata `motore`, prima degli esemplari, fino al verde della sua suite di conformità, e lo fa rientrare con la stessa procedura di tutti. Chi lo usa lo troverà vero, non uno stub. Tag `build/incremento-<n>/motore`.

## Esemplari e prova a secco (8.12)

Per ogni archetipo, la sessione costruisce l'esemplare, backend e frontend, contro i suoi oracoli, fino al verde su tutti i criteri del task. Lavora su un ramo dedicato e lo fa rientrare con la stessa procedura di tutti: le regole valgono anche per chi le applica.

L'esemplare verrà copiato, difetti compresi. Quindi deve essere esemplare davvero: idiomatico per lo stack, con la gestione degli errori del kernel, con i test della propria logica oltre agli oracoli, con tutti gli stati dell'interfaccia, senza scorciatoie "tanto è il primo". Poi:

1. aggiorna il generatore dell'archetipo, così i costruttori partono da codice generato già vicino all'esemplare;
2. scrivi in `CLAUDE.md` la **scheda dell'esemplare**: cinque-dieci righe che dicono quali file guardare per quale aspetto, senza ripetere il codice;
3. togli le voci dell'esemplare dall'elenco d'attesa, nello stesso commit del rientro.

**Prova a secco.** Un costruttore nuovo, del lato più rischioso, riceve il brief per un modulo usa e getta di un archetipo, per esempio una risorsa banale "prova". Ha a disposizione solo `CLAUDE.md`, l'esemplare e il generatore, nessuna spiegazione in più. Osserva: ha usato il generatore? ha seguito i pattern dell'esemplare o ne ha inventati? ha rispettato l'ownership? ha scritto un esito valido? dove la documentazione era ambigua, ha fatto un'escalation o ha tirato a indovinare? Ogni deviazione è un difetto della documentazione, del generatore o del brief, non del costruttore: correggilo ora, e ripeti la prova una volta se le correzioni sono state sostanziali. Il ramo non rientra, e si cancella. È il test di manutenibilità anticipato.

**Approvazione.** Sul branch d'integrazione ogni comando del piano è verde e in elenco d'attesa restano solo i moduli dell'ondata di costruzione. Scrivi `.build/esemplari.md` con `assets/brief-esemplari.md` e portalo all'utente: approva i pattern che verranno replicati in ogni modulo e un campione degli oracoli, cioè la definizione di "fatto". È l'ultimo momento in cui un cambio di direzione costa un esemplare e non dieci moduli. Con il sì: tag `build/incremento-<n>/esemplari` e chiusura della 8.12 con il brief e il tag.

## Ondata di costruzione

I task `costruzione` del piano, lanciati come in `delega-ed-esito.md`, entro il limite di concorrenza deciso nel controllo preliminare, ciascuno con la parte comune di `assets/brief-costruttore.md` e il fascio del task. Ogni costruttore lavora contro oracoli già scritti, parte dal generatore del suo archetipo, e chiude scrivendo il file d'esito.

I rami rientrano uno alla volta, man mano che arrivano (`rientro.md`). Quando un modulo backend rientra verde, il suo frontend passa dal mock al reale. I fallimenti tornano al proprietario, per al massimo due tentativi; le cause si contano, per far scattare l'interruttore sistemico; le escalation non bloccanti si portano all'utente a fine ondata. Chiude l'ondata la suite completa più la CI. Tag `build/incremento-<n>/costruzione`.

## Elenco d'attesa vuoto (8.13)

A ondata chiusa l'elenco dei moduli in attesa è vuoto: nessun oracolo è escluso dalla suite, e "verde" significa ciò che sembra. Se resta una voce, c'è un modulo non rientrato: è un'escalation, non una voce da togliere a mano.

## Controlli sull'intera base (8.02–8.10)

Sul branch d'integrazione, a costruzione chiusa, ciascuno con la sua evidenza:

- **8.02** linter, formatter e analisi statica attivi in pipeline su tutto il codice: il job della CI;
- **8.03** nessun problema bloccante da SAST e SCA: il rapporto degli strumenti;
- **8.04** licenze di tutte le dipendenze verificate e compatibili con la politica: il comando di verifica;
- **8.05** SBOM aggiornata all'ultima build, se il profilo la chiede;
- **8.06** verifica automatica dei segreti attiva, nessun segreto nel repository;
- **8.07** build riproducibile da qualunque commit: una build da un checkout pulito di un commit precedente;
- **8.08** feature flag temporanei rimossi o con una data di rimozione;
- **8.09** registro del debito aggiornato: il debito introdotto in costruzione, dai `dedotto` e dai `fuori_scope` degli esiti, va in `[[debito]]` con motivo, segnale e rientro, e l'utente lo accetta;
- **8.10** documentazione tecnica allineata al codice: README, `CLAUDE.md`, commenti degli strumenti generati.

## DoD e gate (8.01)

Ogni task è rientrato passando le voci della DoD di livello `task`, che il rientro verifica. Alla chiusura si verificano quelle di livello `incremento` (`progetto.py checklist --dod`): regressione verde in pipeline, revisione del codice (le lenti della fase 10 la completano), feature incomplete dietro un flag, incremento deployabile. L'accettazione dell'utente è la voce 11.08, e la nota della chiusura lo dice. La 8.01 si chiude con il registro di build (`scripts/registro.py riepilogo`) e i tag delle ondate.

Il brief del gate: task rientrati e respinti con le cause, interruttori scattati, escalation decise, debito registrato, esiti dei controlli sull'intera base. Con l'approvazione dell'utente, `progetto.py approva 8 --da <chi approva>`.
