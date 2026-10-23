"""Test di verifica_ownership.py. Esecuzione: python -m unittest discover -s scripts -p "test_*.py"."""
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import verifica_ownership as vo  # noqa: E402

SCRIPT = Path(__file__).parent / "verifica_ownership.py"

PIANO = textwrap.dedent("""
    [progetto]
    nome = "Prova"
    branch_integrazione = "main"
    verdetto = "tre-giorni"
    percorsi_e2e = ["tests/e2e/**"]
    intoccabili = ["composer.lock", "contracts/**"]

    [[moduli]]
    id = "veicoli"
    archetipo = "crud"
    rischio = "standard"
    oracoli = ["tests/Oracoli/Veicoli/**"]

    [[moduli]]
    id = "fatture"
    archetipo = "crud"
    rischio = "alto"
    oracoli = ["tests/Oracoli/Fatture/**"]

    [[task]]
    id = "C-veicoli-be"
    ondata = "costruzione"
    agente = "backend-builder"
    modulo = "veicoli"
    possiede = ["app/Moduli/Veicoli/**", "docs/veicoli.md"]
    criteri = ["modulo_backend"]

    [[task]]
    id = "C-fatture-be"
    ondata = "costruzione"
    agente = "backend-builder"
    modulo = "fatture"
    possiede = ["app/Moduli/Fatture/**"]
    criteri = ["modulo_backend"]
""")


def piano():
    return tomllib.loads(PIANO)


def git(*argomenti, cwd):
    subprocess.run(["git", *argomenti], cwd=cwd, check=True, capture_output=True, text=True)


def scrivi(radice, percorso, testo="x\n"):
    f = Path(radice) / percorso
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(testo, encoding="utf-8")


class TestCorrisponde(unittest.TestCase):
    def test_cartella(self):
        self.assertTrue(vo.corrisponde("app/Moduli/Veicoli/A.php", "app/Moduli/Veicoli/**"))
        self.assertFalse(vo.corrisponde("app/Moduli/VeicoliExtra/A.php", "app/Moduli/Veicoli/**"))

    def test_file_esatto(self):
        self.assertTrue(vo.corrisponde("docs/veicoli.md", "docs/veicoli.md"))
        self.assertFalse(vo.corrisponde("docs/veicoli.md.bak", "docs/veicoli.md"))


class TestVerifica(unittest.TestCase):
    def test_solo_percorsi_del_task(self):
        self.assertEqual(vo.verifica(piano(), "C-veicoli-be", ["app/Moduli/Veicoli/A.php", "docs/veicoli.md"]), [])

    def test_intoccabile(self):
        [(p, motivo)] = vo.verifica(piano(), "C-veicoli-be", ["composer.lock"])
        self.assertIn("intoccabile", motivo)

    def test_oracolo(self):
        [(p, motivo)] = vo.verifica(piano(), "C-veicoli-be", ["tests/Oracoli/Veicoli/CreaTest.php"])
        self.assertIn("oracolo del modulo 'veicoli'", motivo)

    def test_e2e(self):
        [(p, motivo)] = vo.verifica(piano(), "C-veicoli-be", ["tests/e2e/percorso/a.spec.ts"])
        self.assertIn("end-to-end", motivo)

    def test_percorso_di_un_altro_task(self):
        [(p, motivo)] = vo.verifica(piano(), "C-veicoli-be", ["app/Moduli/Fatture/X.php"])
        self.assertIn("C-fatture-be", motivo)

    def test_percorso_di_nessuno(self):
        [(p, motivo)] = vo.verifica(piano(), "C-veicoli-be", ["README.md"])
        self.assertIn("fuori dai percorsi", motivo)

    def test_task_assente(self):
        with self.assertRaises(KeyError):
            vo.verifica(piano(), "C-fantasma", [])


class TestConGit(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.dir.name)
        git("init", "-q", "-b", "main", cwd=self.repo)
        git("config", "user.email", "test@example.com", cwd=self.repo)
        git("config", "user.name", "Test", cwd=self.repo)
        scrivi(self.repo, "app/Moduli/Veicoli/A.php")
        scrivi(self.repo, "composer.lock")
        # Come prescrive il metodo: .build/ è esclusa da git tramite info/exclude.
        with (self.repo / ".git" / "info" / "exclude").open("a", encoding="utf-8") as f:
            f.write(".build/\n")
        (self.repo / ".build").mkdir()
        (self.repo / ".build" / "piano.toml").write_text(PIANO, encoding="utf-8")
        git("add", "-A", cwd=self.repo)
        git("commit", "-q", "-m", "base", cwd=self.repo)
        git("checkout", "-q", "-b", "task-veicoli", cwd=self.repo)

    def tearDown(self):
        self.dir.cleanup()

    def esegui(self, *argomenti):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--piano", ".build/piano.toml", "--task", "C-veicoli-be", *argomenti],
            cwd=self.repo, capture_output=True, text=True,
        )
        return r.returncode, r.stdout, r.stderr

    def committa(self, messaggio="lavoro"):
        git("add", "-A", cwd=self.repo)
        git("commit", "-q", "-m", messaggio, cwd=self.repo)

    def test_ramo_pulito(self):
        scrivi(self.repo, "app/Moduli/Veicoli/B.php")
        self.committa()
        codice, out, _ = self.esegui("--base", "main", "--ramo", "task-veicoli")
        self.assertEqual(codice, 0, out)

    def test_ramo_che_tocca_il_lockfile(self):
        scrivi(self.repo, "composer.lock", "cambiato\n")
        self.committa()
        codice, out, _ = self.esegui("--base", "main", "--ramo", "task-veicoli")
        self.assertEqual(codice, 1)
        self.assertIn("composer.lock", out)

    def test_spostamento_fuori_dalla_cartella_e_una_violazione(self):
        git("mv", "app/Moduli/Veicoli/A.php", "app/A.php", cwd=self.repo)
        git("commit", "-q", "-m", "sposta", cwd=self.repo)
        codice, out, _ = self.esegui("--base", "main", "--ramo", "task-veicoli")
        self.assertEqual(codice, 1)
        self.assertIn("app/A.php", out)

    def test_ramo_senza_modifiche(self):
        codice, out, _ = self.esegui("--base", "main", "--ramo", "task-veicoli")
        self.assertEqual(codice, 1)
        self.assertIn("non contiene modifiche", out)

    def test_ramo_inesistente_e_errore_d_uso(self):
        codice, _, err = self.esegui("--base", "main", "--ramo", "non-esiste")
        self.assertEqual(codice, 2)
        self.assertTrue(err)

    def test_percorsi_espliciti_e_json(self):
        codice, out, _ = self.esegui("--percorsi", "app/Moduli/Veicoli/C.php", "--json")
        self.assertEqual(codice, 0)
        self.assertIn('"violazioni": []', out)


if __name__ == "__main__":
    unittest.main()
