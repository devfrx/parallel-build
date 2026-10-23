# Template del report di consegna

Il report descrive ciò che è stato consegnato, non ciò che il piano prometteva. L'ordine conta: chi legge deve incontrare per prima cosa ciò che può fare danno. Togli le sezioni vuote; le uniche sempre presenti sono *Stato in una riga*, *Verificato* e *Non verificato*.

---

```markdown
# Report di consegna — <nome dell'app> (<YYYY-MM-DD>)

## Stato in una riga
<es. "Completa secondo la Definition of Done: 12/12 storie must verdi; deploy
in staging non provato.">

## ⚠️ Da sapere subito
<rischi accettati, voci della PRR non verificabili in locale, escalation
aperte. Se non c'è nulla, togli la sezione.>

## Cosa è stato costruito
| Storia | Priorità | Esito | Test |
|---|---|---|---|

## Verificato
<una riga per verifica: comando o test, esito, quando>
- `<suite>`: verde, <data e ora>, commit <sha>
- `<e2e>`: <N> percorsi verdi
- CI: verde su <branch>, run <id>

## Dedotto
<ciò che si ritiene vero senza averlo eseguito, con il perché>

## Non verificato
<ciò che non è stato verificato, perché, e cosa serve per verificarlo>

## Rischi accettati
| Rischio | Chi l'ha accettato | Quando | Motivo |
|---|---|---|---|

## Escalation aperte e backlog
- <escalation non risolta, con le opzioni>
- Backlog per la versione successiva: <voci da .build/backlog.md>

## Production readiness review
<sintesi: N voci verificate, N non verificabili in locale, N non applicabili;
le non verificabili, elencate>

## Metriche dal registro
<da `registro.py riepilogo`: durata per ondata, rientri riusciti e respinti,
tentativi medi e massimi, escalation, interruttori, cause più frequenti>

## Documentazione
<cosa è stato aggiornato: ADR (stato), docs/design/, README, runbook,
CLAUDE.md, documenti di conformità>

## Come proseguire
<i primi passi consigliati: verifiche mancanti, backlog prioritario>
```
