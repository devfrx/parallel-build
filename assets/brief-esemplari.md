# Template del brief degli esemplari (voce 8.12)

Si scrive in `docs/consegna/incremento-<n>/esemplari.md` e si committa: è l'evidenza della 8.12. Con questa approvazione l'utente accetta due cose che verranno moltiplicate per il numero di moduli: i **pattern** (gli esemplari) e la **definizione di fatto** (gli oracoli). Il brief deve permettergli di guardare il punto giusto in pochi minuti. Togli le sezioni vuote.

---

```markdown
# Esemplari — <nome dell'app>, incremento <n> (<AAAA-MM-GG>)

## Cosa approvi
Gli esemplari, che l'ondata di costruzione replicherà in <N> moduli, e gli
oracoli, che definiscono quando un modulo è finito. Cambiare direzione dopo
questa approvazione costa <N> moduli invece di un esemplare.

## Esemplari
| Archetipo | Modulo | Dove guardare per primo | Scheda in CLAUDE.md |
|---|---|---|---|

Scelte non ovvie fatte negli esemplari:
- <scelta>: <perché> — <file:riga>

## Motore
<se c'è: suite di conformità verde, invarianti provati con test basati su proprietà>

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

## Pronti per l'ondata
- Controllo preliminare: parte 1 e parte 2 passate.
- Tempo del gate incrementale misurato nel controllo preliminare: <minuti> per
  modulo; <N> rientri in serie nell'ondata.
- Concorrenza decisa: <N> agenti per lotto.

## Rischi aperti
<ciò che potrebbe ancora andare storto nell'ondata, e il segnale che lo farà emergere>
```
