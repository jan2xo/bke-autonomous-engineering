import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    path = ROOT / "scripts" / "resolve_intent.py"
    spec = importlib.util.spec_from_file_location("resolve_intent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstructionLibraryContractTests(unittest.TestCase):
    def test_catalog_module_ids_and_paths_are_unique_and_present(self):
        catalog = json.loads((ROOT / "instructions" / "catalog.json").read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in catalog["modules"]]
        paths = [entry["path"] for entry in catalog["modules"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(paths), len(set(paths)))
        for path in paths:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_all_intents_resolve(self):
        resolver = load_resolver()
        for path in sorted((ROOT / "intents").glob("*.json")):
            if path.name == "schema.json":
                continue
            intent = json.loads(path.read_text(encoding="utf-8"))
            result = resolver.resolve(intent["id"], head="abc123")
            self.assertEqual(result["intent"], intent["id"])
            self.assertTrue(result["instruction_digest"])
            self.assertTrue(result["plan_digest"])
            self.assertTrue(result["execution_key"])

    def test_resolution_is_deterministic_and_head_changes_execution_key_only(self):
        resolver = load_resolver()
        one = resolver.resolve("library-maintenance", head="head-one")
        repeat = resolver.resolve("library-maintenance", head="head-one")
        two = resolver.resolve("library-maintenance", head="head-two")
        self.assertEqual(one["instruction_digest"], repeat["instruction_digest"])
        self.assertEqual(one["plan_digest"], repeat["plan_digest"])
        self.assertEqual(one["execution_key"], repeat["execution_key"])
        self.assertEqual(one["instruction_digest"], two["instruction_digest"])
        self.assertEqual(one["plan_digest"], two["plan_digest"])
        self.assertNotEqual(one["execution_key"], two["execution_key"])

    def test_capsule_prefers_compact_actionable_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "verify.log"
            log.write_text("noise\nERROR: test_resolve (tests.Contract)\nAssertionError: missing module id\n", encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts" / "render_ci_capsule.py"),
                "--status", "FAIL",
                "--check", "instruction-library-contract",
                "--intent", "library-maintenance",
                "--head", "abcdef0123456789",
                "--instruction-digest", "1" * 64,
                "--plan-digest", "2" * 64,
                "--run-id", "42",
                "--log", str(log),
            ]
            output = subprocess.check_output(command, text=True)
            visible = [line for line in output.splitlines() if not line.startswith("<!--")]
            self.assertEqual(len(visible), 2)
            self.assertIn("❌ FAIL | instruction-library-contract |", visible[0])
            self.assertIn("run #42", visible[0])
            self.assertLessEqual(len(visible[0]), 260)


if __name__ == "__main__":
    unittest.main()
