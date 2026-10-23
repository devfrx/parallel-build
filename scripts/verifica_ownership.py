#!/usr/bin/env python3
"""Verifica che un ramo tocchi solo i percorsi che il piano assegna al suo task.

È il controllo meccanico della regola "si scrive in copie isolate, si rientra in
serie": prima del merge, ogni percorso modificato dal ramo deve appartenere al
task. Per ogni violazione dice anche perché è grave: un intoccabile (lockfile,
contratti, migrazioni), un oracolo (test scritti da altri), un test end-to-end,
o un percorso di un altro task.

Limiti dichiarati:
  - controlla i percorsi, non il contenuto: un import degli interni di un altro
    modulo lo trovano le fitness function, non questo script
  - legge dal piano solo ciò che gli serve; la validità complessiva del piano è
    compito di valida_piano.py di app-blueprint

Uso, dalla radice del checkout principale:
  python verifica_ownership.py --piano .build/piano.toml --task C-veicoli-be \\
      --base main --ramo <ramo-del-worktree>
  python verifica_ownership.py --piano .build/piano.toml --task C-veicoli-be \\
      --percorsi app/Moduli/Veicoli/Servizio.php composer.lock

Esito: 0 il ramo tocca solo percorsi del task; 1 violazioni, oppure ramo senza
modifiche; 2 errore d'uso (piano o task assente, git non risponde).
"""
import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path


def corrisponde(percorso, pattern):
    """True se il percorso è descritto dal pattern ('cartella/**' o file esatto).

    Duplicato intenzionale della semantica di valida_piano.py: le due skill si
    installano separatamente e nessuna può importare l'altra.
    """
    if pattern.endswith("/**"):
        return percorso.startswith(pattern[:-3] + "/")
    return percorso == pattern


def percorsi_modificati(base, ramo):
    """Percorsi toccati dal ramo dal punto in cui si è staccato dalla base."""
    # Tre punti: le modifiche del ramo dal merge-base, non la differenza tra le
    # due punte (che includerebbe ciò che è entrato nella base nel frattempo).
    # --no-renames riporta sia il vecchio sia il nuovo percorso di un file
    # spostato: spostare un file fuori dalla propria cartella è una violazione.
    r = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", f"{base}...{ramo}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git diff non è riuscito")
    return [p for p in r.stdout.split("\0") if p]


def verifica(piano, id_task, percorsi):
    """Restituisce l'elenco delle violazioni come coppie (percorso, motivo)."""
    tutti = piano.get("task") or []
    task = next((t for t in tutti if t.get("id") == id_task), None)
    if task is None:
        raise KeyError(id_task)
    possiede = task.get("possiede") or []
    progetto = piano.get("progetto") or {}
    intoccabili = progetto.get("intoccabili") or []
    percorsi_e2e = progetto.get("percorsi_e2e") or []
    stessa_ondata = [t for t in tutti if t.get("ondata") == task.get("ondata") and t.get("id") != id_task]

    violazioni = []
    for p in percorsi:
        if any(corrisponde(p, x) for x in possiede):
            continue
        if any(corrisponde(p, x) for x in intoccabili):
            motivo = "intoccabile: lo congela lo scheletro, toccarlo richiede un'escalation"
        else:
            modulo_oracolo = next(
                (m.get("id") for m in piano.get("moduli") or []
                 if any(corrisponde(p, o) for o in m.get("oracoli") or [])),
                None,
            )
            proprietario = next(
                (t.get("id") for t in stessa_ondata if any(corrisponde(p, x) for x in t.get("possiede") or [])),
                None,
            )
            if modulo_oracolo:
                motivo = f"oracolo del modulo '{modulo_oracolo}': i test scritti da altri non si modificano"
            elif any(corrisponde(p, e) for e in percorsi_e2e):
                motivo = "test end-to-end: appartengono all'ondata e2e"
            elif proprietario:
                motivo = f"appartiene al task '{proprietario}' della stessa ondata"
            else:
                motivo = "fuori dai percorsi del task"
        violazioni.append((p, motivo))
    return violazioni


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verifica l'ownership di un ramo prima del rientro.")
    parser.add_argument("--piano", required=True, help="percorso del piano, di solito .build/piano.toml")
    parser.add_argument("--task", required=True, help="id del task a cui appartiene il ramo")
    sorgente = parser.add_mutually_exclusive_group(required=True)
    sorgente.add_argument("--ramo", help="ramo da verificare (richiede --base)")
    sorgente.add_argument("--percorsi", nargs="+", help="percorsi da verificare, senza git")
    parser.add_argument("--base", help="branch d'integrazione da cui il ramo si è staccato")
    parser.add_argument("--json", action="store_true", help="esito in JSON, per gli script")
    args = parser.parse_args(argv)

    try:
        with Path(args.piano).open("rb") as f:
            piano = tomllib.load(f)
    except FileNotFoundError:
        print(f"Errore d'uso: '{args.piano}' non esiste", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as e:
        print(f"Errore d'uso: TOML non valido: {e}", file=sys.stderr)
        return 2

    if args.ramo:
        if not args.base:
            print("Errore d'uso: --ramo richiede --base", file=sys.stderr)
            return 2
        try:
            percorsi = percorsi_modificati(args.base, args.ramo)
        except (RuntimeError, FileNotFoundError) as e:
            print(f"Errore d'uso: {e}", file=sys.stderr)
            return 2
    else:
        percorsi = args.percorsi

    try:
        violazioni = verifica(piano, args.task, percorsi)
    except KeyError:
        print(f"Errore d'uso: il task '{args.task}' non è nel piano", file=sys.stderr)
        return 2

    vuoto = not percorsi
    if args.json:
        print(json.dumps({
            "task": args.task,
            "percorsi": len(percorsi),
            "vuoto": vuoto,
            "violazioni": [{"percorso": p, "motivo": m} for p, m in violazioni],
        }, ensure_ascii=False, indent=2))
    elif vuoto:
        print(f"Task {args.task}: il ramo non contiene modifiche rispetto alla base. Un task finito ha prodotto qualcosa: verifica.")
    elif violazioni:
        print(f"Task {args.task}: {len(violazioni)} violazioni su {len(percorsi)} percorsi")
        for p, m in violazioni:
            print(f"  - {p}: {m}")
    else:
        print(f"Task {args.task}: {len(percorsi)} percorsi, tutti del task")
    return 1 if (violazioni or vuoto) else 0


if __name__ == "__main__":
    sys.exit(main())
