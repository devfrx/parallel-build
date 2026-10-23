# Production readiness review

Ogni voce ha uno stato e una prova. Gli stati sono tre:

- **verificato**: si cita il comando, il test o il file;
- **non verificabile in locale**: si dice perché, e cosa servirà per verificarla;
- **non applicabile**: si dice perché.

Una voce senza stato è aperta, non "probabilmente a posto". Aggiungi voci specifiche del dominio; togli una voce solo marcandola non applicabile, così chi legge sa che è stata considerata.

---

```markdown
# PRR — <nome dell'app> (<YYYY-MM-DD>)

| Area | Voce | Stato | Prova |
|---|---|---|---|
| Funzionalità | Storie must: test d'accettazione verdi | | matrice di tracciabilità |
| Funzionalità | Percorsi critici end-to-end verdi | | `e2e` |
| Funzionalità | Elenco dei moduli in attesa vuoto | | file e `git log` |
| Sicurezza | Test di autorizzazione dalla matrice verdi, incluse le condizioni di proprietà | | |
| Sicurezza | Findings P0/P1 della lente sicurezza chiusi o accettati | | |
| Sicurezza | Nessun segreto nel repository | | scansione dei segreti |
| Sicurezza | Gestione dei segreti in esercizio definita | | |
| Supply chain | Audit vulnerabilità senza alte o critiche aperte | | `supply_chain` |
| Supply chain | Licenze conformi alla politica, SBOM generato | | |
| Dati | Migrazioni applicabili da zero e in avanti | | |
| Dati | Backup e ripristino provati (RPO/RTO dell'intake) | | |
| Dati | Conservazione e cancellazione dei dati personali | | |
| Affidabilità | Errori secondo il modello unico, nessun errore inghiottito | | |
| Affidabilità | Servizi esterni con timeout, tentativi, idempotenza | | |
| Osservabilità | Log strutturati secondo le convenzioni, senza dati personali | | |
| Osservabilità | Metriche e controlli di salute esposti | | |
| Osservabilità | Allarmi sui sintomi dei percorsi critici | | |
| Prestazioni | Scenari misurabili dell'intake verificati, con quale carico | | |
| Prestazioni | Liste paginate, query dei percorsi critici indicizzate | | |
| Accessibilità | WCAG 2.2 AA sui percorsi critici | | revisione UI e test |
| Deploy | Pipeline di deploy verso staging provata | | |
| Deploy | Configurazione per ambiente, nessun valore di sviluppo in esercizio | | |
| Deploy | Procedura di rollback scritta e provata | | runbook |
| Documentazione | README, runbook, ADR aggiornati, `docs/design/` allineato | | |
| Conformità | Documenti privacy rivisti da un professionista, se servono | | `compliance-docs` |
| Manutenibilità | Test di manutenibilità superato | | |
```
