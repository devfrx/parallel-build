#!/usr/bin/env python3
"""Valida il file d'esito che un sotto-agente scrive alla fine del suo task.

L'esito è una dichiarazione, non un fatto: l'orchestratore rieseguirà comunque
i gate. Questo script controlla che la dichiarazione sia completa e coerente
prima di spendere tempo nel rientro:
  1. schema fisso: campi obbligatori, tipi, valori ammessi, nessun campo ignoto
  2. coerenza: un esito "completato" non ha verifiche fallite né decisioni
     bloccanti; "parziale" e "bloccato" dicono perché; "bloccato" ha almeno una
     decisione bloccante
  3. con --piano: l'esito è del task giusto, e un esito "completato" riporta come
     passato ogni criterio che il piano assegna al task

Campi dell'esito (JSON):
  task, esito (completato | parziale | bloccato), ramo, commit (hash 7-40 hex),
  motivo (obbligatorio se l'esito non è "completato"),
  fatto [testo], verificato [{comando, risultato: passato | fallito, criterio?, note?}],
  dedotto [testo], fuori_scope [testo],
  da_decidere [{domanda, opzioni [testo], bloccante: bool, raccomandazione?}],
  candidati_promozione [testo] (facoltativo), documentazione_design (testo)

Uso:
  python valida_esito.py <worktree>/.build/esiti/C-veicoli-be.json
  python valida_esito.py <file> --piano .build/piano.toml --task C-veicoli-be

Esito: 0 esito valido; 1 esito da correggere; 2 errore d'uso (file assente,
JSON o TOML non valido, task assente dal piano).
"""
import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ESITI = {"completato", "parziale", "bloccato"}
RISULTATI = {"passato", "fallito"}
OBBLIGATORI = {
    "task": str, "esito": str, "ramo": str, "commit": str, "fatto": list, "verificato": list,
    "dedotto": list, "fuori_scope": list, "da_decidere": list, "documentazione_design": str,
}
FACOLTATIVI = {"motivo": str, "candidati_promozione": list}
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


def _testi(valore):
    return isinstance(valore, list) and all(isinstance(x, str) and x.strip() for x in valore)


def valida(esito, criteri_task=None, id_task=None):
    """Restituisce l'elenco degli errori di un esito già letto."""
    if not isinstance(esito, dict):
        return ["l'esito deve essere un oggetto JSON"]
    errori = []
    for campo, tipo in OBBLIGATORI.items():
        if campo not in esito:
            errori.append(f"manca il campo '{campo}'")
        elif not isinstance(esito[campo], tipo):
            errori.append(f"'{campo}' deve essere di tipo {tipo.__name__}")
    for campo, tipo in FACOLTATIVI.items():
        if campo in esito and not isinstance(esito[campo], tipo):
            errori.append(f"'{campo}' deve essere di tipo {tipo.__name__}")
    ignoti = set(esito) - set(OBBLIGATORI) - set(FACOLTATIVI)
    for campo in sorted(ignoti):
        errori.append(f"campo ignoto '{campo}': lo schema è fisso, perché l'orchestratore lo legge con uno script")
    if errori:
        return errori

    if esito["esito"] not in ESITI:
        errori.append(f"'esito' deve essere uno tra {sorted(ESITI)}")
    if not esito["task"].strip() or not esito["ramo"].strip():
        errori.append("'task' e 'ramo' non possono essere vuoti")
    if not COMMIT.match(esito["commit"]):
        errori.append("'commit' deve essere un hash git (7-40 caratteri esadecimali minuscoli)")
    for campo in ("fatto", "dedotto", "fuori_scope"):
        if not _testi(esito[campo]) and esito[campo]:
            errori.append(f"'{campo}' deve contenere solo testi non vuoti")
    if "candidati_promozione" in esito and esito["candidati_promozione"] and not _testi(esito["candidati_promozione"]):
        errori.append("'candidati_promozione' deve contenere solo testi non vuoti")

    passati = set()
    falliti = 0
    for i, v in enumerate(esito["verificato"]):
        if not isinstance(v, dict) or not isinstance(v.get("comando"), str) or not v.get("comando").strip():
            errori.append(f"verificato[{i}]: serve un 'comando' testuale")
            continue
        if v.get("risultato") not in RISULTATI:
            errori.append(f"verificato[{i}]: 'risultato' deve essere uno tra {sorted(RISULTATI)}")
            continue
        ignoti_v = set(v) - {"comando", "risultato", "criterio", "note"}
        if ignoti_v:
            errori.append(f"verificato[{i}]: campi ignoti {sorted(ignoti_v)}")
        if v["risultato"] == "fallito":
            falliti += 1
        elif isinstance(v.get("criterio"), str):
            passati.add(v["criterio"])

    bloccanti = 0
    for i, d in enumerate(esito["da_decidere"]):
        if not isinstance(d, dict) or not isinstance(d.get("domanda"), str) or not d.get("domanda").strip():
            errori.append(f"da_decidere[{i}]: serve una 'domanda' testuale")
            continue
        if not isinstance(d.get("bloccante"), bool):
            errori.append(f"da_decidere[{i}]: 'bloccante' deve essere true o false")
        elif d["bloccante"]:
            bloccanti += 1
        if not _testi(d.get("opzioni")) or len(d.get("opzioni")) < 1:
            errori.append(f"da_decidere[{i}]: elenca le opzioni individuate, almeno una")

    stato = esito["esito"]
    if stato == "completato":
        if not esito["fatto"]:
            errori.append("un esito 'completato' dice cosa è stato fatto")
        if not esito["verificato"]:
            errori.append("un esito 'completato' riporta le verifiche eseguite")
        if falliti:
            errori.append(f"un esito 'completato' non può avere verifiche fallite ({falliti})")
        if bloccanti:
            errori.append("un esito 'completato' non può avere decisioni bloccanti aperte")
    elif stato in ("parziale", "bloccato"):
        if not isinstance(esito.get("motivo"), str) or not esito["motivo"].strip():
            errori.append(f"un esito '{stato}' dice perché nel campo 'motivo'")
        if stato == "bloccato" and not bloccanti:
            errori.append("un esito 'bloccato' ha almeno una decisione bloccante in 'da_decidere'")

    if id_task is not None and esito["task"] != id_task:
        errori.append(f"l'esito è del task '{esito['task']}', non di '{id_task}'")
    if criteri_task is not None and stato == "completato":
        mancanti = [c for c in criteri_task if c not in passati]
        if mancanti:
            errori.append(f"criteri del task non riportati come passati: {', '.join(mancanti)}")
    return errori


def main(argv=None):
    parser = argparse.ArgumentParser(description="Valida il file d'esito di un sotto-agente.")
    parser.add_argument("esito", help="percorso del file d'esito JSON")
    parser.add_argument("--piano", help="piano TOML, per controllare task e criteri")
    parser.add_argument("--task", help="id del task atteso (richiesto con --piano)")
    args = parser.parse_args(argv)

    try:
        esito = json.loads(Path(args.esito).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Errore d'uso: '{args.esito}' non esiste", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Errore d'uso: JSON non valido: {e}", file=sys.stderr)
        return 2

    criteri = None
    if args.piano:
        if not args.task:
            print("Errore d'uso: --piano richiede --task", file=sys.stderr)
            return 2
        try:
            with Path(args.piano).open("rb") as f:
                piano = tomllib.load(f)
        except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
            print(f"Errore d'uso: piano non leggibile: {e}", file=sys.stderr)
            return 2
        task = next((t for t in piano.get("task") or [] if t.get("id") == args.task), None)
        if task is None:
            print(f"Errore d'uso: il task '{args.task}' non è nel piano", file=sys.stderr)
            return 2
        criteri = task.get("criteri") or []

    errori = valida(esito, criteri, args.task)
    if errori:
        print(f"Esito da correggere ({len(errori)} problemi):")
        for e in errori:
            print(f"  - {e}")
        return 1
    print(f"Esito valido: task {esito['task']}, {esito['esito']}, commit {esito['commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
