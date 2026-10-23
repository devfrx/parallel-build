#!/usr/bin/env python3
"""Registro di build: eventi della costruzione in JSON Lines, e il loro riepilogo.

Il registro è la memoria misurabile del metodo. Serve tre volte: durante la
costruzione, per vedere dove si è e quante volte un task è tornato indietro; in
chiusura, per il report; dopo, per la retrospettiva e il banco di prova, che
confrontano le esecuzioni tra versioni della skill. Ogni evento è una riga JSON
con un istante UTC: si aggiunge, non si riscrive.

Eventi e campi richiesti (tentativo, nota e istante sono sempre facoltativi):
  preflight      esito
  gate           gate, esito
  ondata_inizio  ondata
  ondata_fine    ondata
  delega         task, ondata          (anche le riprese per correzione)
  rientro_ok     task, ondata
  rientro_ko     task, ondata, causa
  escalation     task, ondata          (--bloccante se ferma il task)
  interruttore   ondata, causa
  decisione      nota
  cambiamento    nota
  nota           nota

Uso:
  python registro.py aggiungi --registro .build/registro.jsonl --evento delega \\
      --task C-veicoli-be --ondata costruzione
  python registro.py aggiungi --registro .build/registro.jsonl --evento rientro_ko \\
      --task C-veicoli-be --ondata costruzione --causa "contratto: formato errori"
  python registro.py riepilogo --registro .build/registro.jsonl [--json]

Esito: 0 fatto; 2 errore d'uso (campi mancanti, registro assente o con righe
non valide).
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RICHIESTI = {
    "preflight": ("esito",),
    "gate": ("gate", "esito"),
    "ondata_inizio": ("ondata",),
    "ondata_fine": ("ondata",),
    "delega": ("task", "ondata"),
    "rientro_ok": ("task", "ondata"),
    "rientro_ko": ("task", "ondata", "causa"),
    "escalation": ("task", "ondata"),
    "interruttore": ("ondata", "causa"),
    "decisione": ("nota",),
    "cambiamento": ("nota",),
    "nota": ("nota",),
}
ESITI = ("passato", "fallito")
CAMPI = ("task", "ondata", "esito", "gate", "causa", "tentativo", "nota")


def adesso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def crea_evento(evento, **campi):
    """Costruisce un evento validato. Solleva ValueError se mancano campi."""
    if evento not in RICHIESTI:
        raise ValueError(f"evento sconosciuto '{evento}'")
    mancanti = [c for c in RICHIESTI[evento] if campi.get(c) in (None, "")]
    if mancanti:
        raise ValueError(f"l'evento '{evento}' richiede: {', '.join(mancanti)}")
    if campi.get("esito") is not None and campi["esito"] not in ESITI:
        raise ValueError(f"'esito' deve essere uno tra {list(ESITI)}")
    istante = campi.get("istante") or adesso()
    try:
        datetime.fromisoformat(istante)
    except ValueError:
        raise ValueError(f"istante non valido '{istante}': usa ISO 8601, per esempio 2026-10-01T09:00:00Z")
    riga = {"istante": istante, "evento": evento}
    for c in CAMPI:
        if campi.get(c) not in (None, ""):
            riga[c] = campi[c]
    if evento == "escalation":
        riga["bloccante"] = bool(campi.get("bloccante"))
    return riga


def leggi(percorso):
    """Legge il registro. Solleva ValueError indicando la riga non valida."""
    eventi = []
    for n, testo in enumerate(Path(percorso).read_text(encoding="utf-8").splitlines(), start=1):
        if not testo.strip():
            continue
        try:
            e = json.loads(testo)
        except json.JSONDecodeError:
            raise ValueError(f"riga {n}: JSON non valido")
        if not isinstance(e, dict) or e.get("evento") not in RICHIESTI or "istante" not in e:
            raise ValueError(f"riga {n}: non è un evento del registro")
        eventi.append(e)
    return eventi


def _minuti(inizio, fine):
    delta = datetime.fromisoformat(fine) - datetime.fromisoformat(inizio)
    return round(delta.total_seconds() / 60)


def riepiloga(eventi):
    """Riepilogo per ondata e complessivo, pronto per il report e la retrospettiva."""
    ondate = {}

    def ondata(nome):
        return ondate.setdefault(nome, {
            "deleghe": 0, "rientri_ok": 0, "rientri_ko": 0, "escalation": 0, "escalation_bloccanti": 0,
            "interruttori": 0, "tentativi": Counter(), "inizio": None, "fine": None,
        })

    cause = Counter()
    gate = []
    preflight = None
    decisioni = cambiamenti = 0
    for e in eventi:
        tipo = e["evento"]
        if tipo == "preflight":
            preflight = e.get("esito")
        elif tipo == "gate":
            gate.append({"gate": e.get("gate"), "esito": e.get("esito"), "istante": e["istante"]})
        elif tipo == "decisione":
            decisioni += 1
        elif tipo == "cambiamento":
            cambiamenti += 1
        elif "ondata" in e:
            o = ondata(e["ondata"])
            if tipo == "ondata_inizio":
                o["inizio"] = o["inizio"] or e["istante"]
            elif tipo == "ondata_fine":
                o["fine"] = e["istante"]
            elif tipo == "delega":
                o["deleghe"] += 1
                o["tentativi"][e["task"]] += 1
            elif tipo == "rientro_ok":
                o["rientri_ok"] += 1
            elif tipo == "rientro_ko":
                o["rientri_ko"] += 1
                cause[e["causa"]] += 1
            elif tipo == "escalation":
                o["escalation"] += 1
                o["escalation_bloccanti"] += 1 if e.get("bloccante") else 0
            elif tipo == "interruttore":
                o["interruttori"] += 1
                cause[f"interruttore: {e['causa']}"] += 1

    per_ondata = {}
    for nome, o in ondate.items():
        tentativi = list(o["tentativi"].values())
        per_ondata[nome] = {
            "task": len(tentativi),
            "deleghe": o["deleghe"],
            "rientri_ok": o["rientri_ok"],
            "rientri_ko": o["rientri_ko"],
            "tentativi_max": max(tentativi) if tentativi else 0,
            "tentativi_medi": round(sum(tentativi) / len(tentativi), 2) if tentativi else 0,
            "escalation": o["escalation"],
            "escalation_bloccanti": o["escalation_bloccanti"],
            "interruttori": o["interruttori"],
            "durata_minuti": _minuti(o["inizio"], o["fine"]) if o["inizio"] and o["fine"] else None,
        }
    return {
        "eventi": len(eventi),
        "preflight": preflight,
        "gate": gate,
        "ondate": per_ondata,
        "cause_piu_frequenti": cause.most_common(5),
        "decisioni": decisioni,
        "cambiamenti": cambiamenti,
    }


def stampa(r):
    print(f"Registro: {r['eventi']} eventi — preflight: {r['preflight'] or 'non registrato'}")
    for g in r["gate"]:
        print(f"  gate {g['gate']}: {g['esito']} ({g['istante']})")
    for nome, o in r["ondate"].items():
        durata = f"{o['durata_minuti']} min" if o["durata_minuti"] is not None else "durata non chiusa"
        print(f"\nOndata {nome} — {durata}")
        print(f"  task {o['task']}, deleghe {o['deleghe']}, rientri ok {o['rientri_ok']} / ko {o['rientri_ko']}")
        print(f"  tentativi per task: max {o['tentativi_max']}, medi {o['tentativi_medi']}")
        print(f"  escalation {o['escalation']} (bloccanti {o['escalation_bloccanti']}), interruttori {o['interruttori']}")
    if r["cause_piu_frequenti"]:
        print("\nCause più frequenti di ritorno:")
        for causa, n in r["cause_piu_frequenti"]:
            print(f"  {n} × {causa}")
    print(f"\nDecisioni registrate {r['decisioni']}, cambiamenti {r['cambiamenti']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Registro di build del metodo di costruzione parallela.")
    sotto = parser.add_subparsers(dest="comando", required=True)

    agg = sotto.add_parser("aggiungi", help="aggiunge un evento")
    agg.add_argument("--registro", required=True)
    agg.add_argument("--evento", required=True, choices=sorted(RICHIESTI))
    for campo in ("task", "ondata", "esito", "gate", "causa", "nota", "istante"):
        agg.add_argument(f"--{campo}")
    agg.add_argument("--tentativo", type=int)
    agg.add_argument("--bloccante", action="store_true")

    rie = sotto.add_parser("riepilogo", help="riepiloga il registro")
    rie.add_argument("--registro", required=True)
    rie.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.comando == "aggiungi":
        try:
            riga = crea_evento(
                args.evento, task=args.task, ondata=args.ondata, esito=args.esito, gate=args.gate,
                causa=args.causa, nota=args.nota, istante=args.istante, tentativo=args.tentativo,
                bloccante=args.bloccante,
            )
        except ValueError as e:
            print(f"Errore d'uso: {e}", file=sys.stderr)
            return 2
        percorso = Path(args.registro)
        percorso.parent.mkdir(parents=True, exist_ok=True)
        with percorso.open("a", encoding="utf-8") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
        return 0

    try:
        eventi = leggi(args.registro)
    except FileNotFoundError:
        print(f"Errore d'uso: '{args.registro}' non esiste", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Errore d'uso: {e}", file=sys.stderr)
        return 2
    r = riepiloga(eventi)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        stampa(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
