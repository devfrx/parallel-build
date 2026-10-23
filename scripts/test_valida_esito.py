"""Test di valida_esito.py. Esecuzione: python -m unittest discover -s scripts -p "test_*.py"."""
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import valida_esito as ve  # noqa: E402

SCRIPT = Path(__file__).parent / "valida_esito.py"
ESEMPIO = Path(__file__).parent.parent / "assets" / "esito-esempio.json"
CRITERI = ["modulo_backend", "fitness", "lint"]


def esempio():
    return json.loads(ESEMPIO.read_text(encoding="utf-8"))


def contiene(errori, frammento):
    return any(frammento in e for e in errori)


class TestRossoAtteso(unittest.TestCase):
    def esito_oracoli(self, note="14 asserzioni false; nessun errore di sintassi, import o configurazione"):
        e = esempio()
        e["task"] = "O-veicoli"
        e["verificato"] = [{"criterio": "lint", "comando": "composer lint && npm run lint", "risultato": "passato"},
                           {"comando": "composer test:modulo -- veicoli", "risultato": "rosso-atteso", "note": note}]
        return e

    def test_gli_oracoli_consegnano_test_rossi(self):
        self.assertEqual(ve.valida(self.esito_oracoli(), ["lint"], "O-veicoli", "oracoli"), [])

    def test_il_rosso_atteso_dice_perche(self):
        self.assertTrue(contiene(ve.valida(self.esito_oracoli(note=""), ["lint"], "O-veicoli", "oracoli"),
                                 "dice nelle note perché fallisce"))

    def test_un_costruttore_non_consegna_test_rossi(self):
        e = esempio()
        e["verificato"].append({"comando": "composer test", "risultato": "rosso-atteso", "note": "manca il codice"})
        self.assertTrue(contiene(ve.valida(e, CRITERI, "C-veicoli-be", "costruzione"),
                                 "solo un task dell'ondata degli oracoli"))


class TestEsempio(unittest.TestCase):
    def test_l_esempio_e_valido_anche_con_i_criteri(self):
        self.assertEqual(ve.valida(esempio(), CRITERI, "C-veicoli-be"), [])


class TestSchema(unittest.TestCase):
    def test_campo_mancante(self):
        e = esempio()
        del e["dedotto"]
        self.assertTrue(contiene(ve.valida(e), "manca il campo 'dedotto'"))

    def test_campo_ignoto(self):
        e = esempio()
        e["umore"] = "ottimo"
        self.assertTrue(contiene(ve.valida(e), "campo ignoto 'umore'"))

    def test_tipo_sbagliato(self):
        e = esempio()
        e["fatto"] = "tutto"
        self.assertTrue(contiene(ve.valida(e), "'fatto' deve essere di tipo list"))

    def test_commit_non_valido(self):
        e = esempio()
        e["commit"] = "HEAD"
        self.assertTrue(contiene(ve.valida(e), "hash git"))

    def test_risultato_non_ammesso(self):
        e = esempio()
        e["verificato"][0]["risultato"] = "quasi"
        self.assertTrue(contiene(ve.valida(e), "'risultato' deve essere"))

    def test_decisione_senza_opzioni(self):
        e = esempio()
        e["da_decidere"][0]["opzioni"] = []
        self.assertTrue(contiene(ve.valida(e), "elenca le opzioni"))


class TestCoerenza(unittest.TestCase):
    def test_completato_con_verifica_fallita(self):
        e = esempio()
        e["verificato"][1]["risultato"] = "fallito"
        self.assertTrue(contiene(ve.valida(e), "verifiche fallite"))

    def test_completato_con_decisione_bloccante(self):
        e = esempio()
        e["da_decidere"][0]["bloccante"] = True
        self.assertTrue(contiene(ve.valida(e), "decisioni bloccanti aperte"))

    def test_parziale_senza_motivo(self):
        e = esempio()
        e["esito"] = "parziale"
        self.assertTrue(contiene(ve.valida(e), "nel campo 'motivo'"))

    def test_bloccato_senza_decisione_bloccante(self):
        e = esempio()
        e.update({"esito": "bloccato", "motivo": "serve una decisione"})
        self.assertTrue(contiene(ve.valida(e), "almeno una decisione bloccante"))

    def test_bloccato_coerente(self):
        e = esempio()
        e.update({"esito": "bloccato", "motivo": "il contratto non dice come trattare i duplicati"})
        e["da_decidere"][0]["bloccante"] = True
        self.assertEqual(ve.valida(e), [])


class TestCriteri(unittest.TestCase):
    def test_criterio_del_piano_non_riportato(self):
        e = esempio()
        e["verificato"] = [v for v in e["verificato"] if v["criterio"] != "fitness"]
        self.assertTrue(contiene(ve.valida(e, CRITERI), "fitness"))

    def test_task_sbagliato(self):
        self.assertTrue(contiene(ve.valida(esempio(), CRITERI, "C-fatture-be"), "non di 'C-fatture-be'"))

    def test_parziale_non_richiede_tutti_i_criteri(self):
        e = esempio()
        e.update({"esito": "parziale", "motivo": "manca la ricerca per targa"})
        e["verificato"] = e["verificato"][:1]
        self.assertEqual(ve.valida(e, CRITERI), [])


class TestRigaDiComando(unittest.TestCase):
    def esegui(self, *argomenti):
        r = subprocess.run([sys.executable, str(SCRIPT), *argomenti], capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def test_esempio_esito_zero(self):
        codice, out, _ = self.esegui(str(ESEMPIO))
        self.assertEqual(codice, 0, out)

    def test_con_piano(self):
        piano = textwrap.dedent("""
            [[task]]
            id = "C-veicoli-be"
            criteri = ["modulo_backend", "fitness", "lint", "typecheck"]
        """)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "piano.toml"
            f.write_text(piano, encoding="utf-8")
            codice, out, _ = self.esegui(str(ESEMPIO), "--piano", str(f), "--task", "C-veicoli-be")
            self.assertEqual(codice, 1)
            self.assertIn("typecheck", out)

    def test_json_non_valido_esito_due(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "esito.json"
            f.write_text("{ non json", encoding="utf-8")
            codice, _, _ = self.esegui(str(f))
            self.assertEqual(codice, 2)

    def test_piano_senza_task_esito_due(self):
        codice, _, err = self.esegui(str(ESEMPIO), "--piano", "piano.toml")
        self.assertEqual(codice, 2)
        self.assertIn("--task", err)


if __name__ == "__main__":
    unittest.main()
