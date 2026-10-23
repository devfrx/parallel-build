# Template del report di consegna

Il report descrive ciò che è stato consegnato, non ciò che il piano prometteva. L'ordine conta: chi legge deve incontrare per prima cosa ciò che può fare danno. Togli le sezioni vuote; le uniche sempre presenti sono *Stato in una riga*, *Verificato* e *Non verificato*.

---

```markdown
# Report di consegna — <nome dell'app>, incremento <n> (<AAAA-MM-GG>)

## Stato in una riga
<es. "Incremento 1 accettato: 17/17 storie verdi; ripristino da backup non
provato in questo ambiente.">

## ⚠️ Da sapere subito
<rischi accettati, voci chiuse come non verificabili in questo ambiente,
escalation aperte. Se non c'è nulla, togli la sezione.>

## Cosa è stato costruito
| Storia | Esito | Test d'accettazione | End-to-end |
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

## Fasi 9–12
<voci chiuse, escluse con il motivo, rinviate al debito di pubblicazione; le
escluse come non verificabili, elencate>

## Escalation, modifiche proposte, debito
- <escalation non risolta, con le opzioni>
- Modifiche proposte durante la costruzione: <MOD-n, in una riga>
- Debito registrato: <DEB-n, in una riga>

## Metriche dal registro
<da `registro.py riepilogo`: durata per ondata, rientri riusciti e respinti,
tentativi medi e massimi, escalation, interruttori, cause più frequenti>

## Documentazione
<cosa è stato aggiornato: README, runbook, CLAUDE.md, ADR (stato), documenti di
conformità; viste della progettazione rigenerate>

## Come proseguire
<i primi passi consigliati: verifiche mancanti, modifiche da valutare,
apertura dell'incremento successivo>
```
