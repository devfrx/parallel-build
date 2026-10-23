"""Test di registro.py. Esecuzione: python -m unittest discover -s scripts -p "test_*.py"."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import registro as rg  # noqa: E402

SCRIPT = Path(__file__).parent / "registro.py"


class TestCreaEvento(unittest.TestCase):
    def test_campi_richiesti(self):
        with self.assertRaises(ValueError):
            rg.crea_evento("rientro_ko", task="C-1", ondata="costruzione")

    def test_esito_non_ammesso(self):
        with self.assertRaises(ValueError):
            rg.crea_evento("preflight", esito="forse")

    def test_istante_non_valido(self):
        with self.assertRaises(ValueError):
            rg.crea_evento("nota", nota="x", istante="ieri")

    def test_escalation_registra_se_e_bloccante(self):
        e = rg.crea_evento("escalation", task="C-1", ondata="costruzione", bloccante=True,
                           istante="2026-10-01T09:00:00Z")
        self.assertTrue(e["bloccante"])
        self.assertEqual(e["istante"], "2026-10-01T09:00:00Z")


class TestRiepilogo(unittest.TestCase):
    def test_conteggi_tentativi_e_durata(self):
        eventi = [
            rg.crea_evento("preflight", esito="passato", istante="2026-10-01T08:00:00Z"),
            rg.crea_evento("ondata_inizio", ondata="costruzione", istante="2026-10-01T09:00:00Z"),
            rg.crea_evento("delega", task="C-1", ondata="costruzione", istante="2026-10-01T09:01:00Z"),
            rg.crea_evento("delega", task="C-2", ondata="costruzione", istante="2026-10-01T09:01:00Z"),
            rg.crea_evento("rientro_ko", task="C-1", ondata="costruzione", causa="formato errori",
                           istante="2026-10-01T10:00:00Z"),
            rg.crea_evento("delega", task="C-1", ondata="costruzione", tentativo=2, istante="2026-10-01T10:05:00Z"),
            rg.crea_evento("rientro_ok", task="C-1", ondata="costruzione", istante="2026-10-01T10:40:00Z"),
            rg.crea_evento("rientro_ok", task="C-2", ondata="costruzione", istante="2026-10-01T10:20:00Z"),
            rg.crea_evento("escalation", task="C-2", ondata="costruzione", istante="2026-10-01T10:20:00Z"),
            rg.crea_evento("ondata_fine", ondata="costruzione", istante="2026-10-01T11:30:00Z"),
            rg.crea_evento("gate", gate="8.12", esito="passato", istante="2026-10-01T08:30:00Z"),
        ]
        r = rg.riepiloga(eventi)
        o = r["ondate"]["costruzione"]
        self.assertEqual(r["preflight"], "passato")
        self.assertEqual(o["task"], 2)
        self.assertEqual(o["deleghe"], 3)
        self.assertEqual((o["rientri_ok"], o["rientri_ko"]), (2, 1))
        self.assertEqual(o["tentativi_max"], 2)
        self.assertEqual(o["tentativi_medi"], 1.5)
        self.assertEqual((o["escalation"], o["escalation_bloccanti"]), (1, 0))
        self.assertEqual(o["durata_minuti"], 150)
        self.assertEqual(r["cause_piu_frequenti"], [("formato errori", 1)])
        self.assertEqual(r["gate"][0]["gate"], "8.12")

    def test_ondata_non_chiusa(self):
        r = rg.riepiloga([rg.crea_evento("ondata_inizio", ondata="e2e", istante="2026-10-01T09:00:00Z")])
        self.assertIsNone(r["ondate"]["e2e"]["durata_minuti"])


class TestRigaDiComando(unittest.TestCase):
    def esegui(self, *argomenti):
        r = subprocess.run([sys.executable, str(SCRIPT), *argomenti], capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def test_aggiungi_e_riepilogo(self):
        with tempfile.TemporaryDirectory() as d:
            reg = str(Path(d) / ".build" / "registro.jsonl")
            for argomenti in (
                ("--evento", "ondata_inizio", "--ondata", "oracoli", "--istante", "2026-10-01T09:00:00Z"),
                ("--evento", "delega", "--task", "O-1", "--ondata", "oracoli", "--istante", "2026-10-01T09:00:00Z"),
                ("--evento", "rientro_ok", "--task", "O-1", "--ondata", "oracoli", "--istante", "2026-10-01T09:30:00Z"),
                ("--evento", "ondata_fine", "--ondata", "oracoli", "--istante", "2026-10-01T09:45:00Z"),
            ):
                codice, _, err = self.esegui("aggiungi", "--registro", reg, *argomenti)
                self.assertEqual(codice, 0, err)
            righe = Path(reg).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(righe), 4)
            codice, out, _ = self.esegui("riepilogo", "--registro", reg, "--json")
            self.assertEqual(codice, 0)
            self.assertEqual(json.loads(out)["ondate"]["oracoli"]["durata_minuti"], 45)

    def test_campo_mancante_esito_due(self):
        with tempfile.TemporaryDirectory() as d:
            codice, _, err = self.esegui("aggiungi", "--registro", str(Path(d) / "r.jsonl"),
                                         "--evento", "interruttore", "--ondata", "costruzione")
            self.assertEqual(codice, 2)
            self.assertIn("causa", err)

    def test_riga_non_valida_esito_due(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Path(d) / "r.jsonl"
            reg.write_text('{"istante": "2026-10-01T09:00:00Z", "evento": "nota", "nota": "ok"}\nnon json\n',
                           encoding="utf-8")
            codice, _, err = self.esegui("riepilogo", "--registro", str(reg))
            self.assertEqual(codice, 2)
            self.assertIn("riga 2", err)

    def test_registro_assente_esito_due(self):
        codice, _, _ = self.esegui("riepilogo", "--registro", "/non/esiste.jsonl")
        self.assertEqual(codice, 2)


if __name__ == "__main__":
    unittest.main()
