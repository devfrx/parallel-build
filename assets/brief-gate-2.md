# Template del brief del gate 2

Al gate 2 l'utente approva due cose che verranno moltiplicate per il numero di moduli: i **pattern** (gli esemplari) e la **definizione di fatto** (gli oracoli). Il brief deve permettergli di guardare il punto giusto in pochi minuti, non di rileggere il giorno. Togli le sezioni vuote.

---

```markdown
# Gate 2 — <nome dell'app> (<YYYY-MM-DD>)

## Cosa approvi
Gli esemplari, che domani verranno replicati in <N> moduli, e gli oracoli, che
definiscono quando un modulo è finito. Cambiare direzione dopo questo gate costa
<N> moduli invece di un esemplare.

## Esemplari
| Archetipo | Modulo | Dove guardare per primo | Scheda in CLAUDE.md |
|---|---|---|---|

Scelte non ovvie fatte negli esemplari:
- <scelta>: <perché> — <file:riga>

## Oracoli: un campione da leggere
- <modulo>: test di autorizzazione su <condizione di proprietà> — <file>
- <modulo ad alto rischio>: <test>
- <test d'interfaccia di un percorso critico>
Numeri: <N> test d'accettazione, <N> di contratto, <N> di autorizzazione, tutti
rossi per la ragione giusta (verificato al rientro).

## Prova a secco
<Esito: cosa il costruttore nuovo ha fatto da solo, dove ha deviato, cosa è
stato corretto in documentazione o generatori. Se è stata ripetuta, l'esito
della ripetizione.>

## Spike
| Spike | Risposta | Prova | Conseguenze |
|---|---|---|---|

## Pronti per domani
- Controllo preliminare: parte 1 e parte 2 passate.
- Tempo del gate incrementale: <minuti> per modulo. Rientro stimato per <N>
  task: <minuti>.
- Concorrenza decisa: <N> agenti per lotto.

## Rischi aperti
<ciò che potrebbe ancora andare storto domani, e il segnale che lo farà emergere>
```
