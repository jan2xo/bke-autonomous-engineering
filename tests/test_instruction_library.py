import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstructionLibraryContractTests(unittest.TestCase):
    def test_catalog_module_ids_and_paths_are_unique_and_present(self):
        resolver = load_script("resolve_intent")
        catalog = json.loads((ROOT / "instructions" / "catalog.json").read_text(encoding="utf-8"))
        catalog_by_id = resolver.validate_catalog(catalog)
        self.assertEqual(len(catalog_by_id), len(catalog["modules"]))
        for entry in catalog["modules"]:
            self.assertTrue((ROOT / entry["path"]).is_file(), entry["path"])

    def test_registry_is_valid_and_dependency_closed(self):
        resolver = load_script("resolve_intent")
        registry = json.loads((ROOT / "checks" / "registry.json").read_text(encoding="utf-8"))
        checks = resolver.validate_check_registry(registry)
        self.assertIn("instruction-library-contract", checks)
        for check_id, entry in checks.items():
            for dep in entry["depends_on"]:
                self.assertIn(dep, checks, f"{check_id} -> {dep}")

    def test_all_intents_resolve_to_executable_plans(self):
        resolver = load_script("resolve_intent")
        for path in sorted((ROOT / "intents").glob("*.json")):
            if path.name == "schema.json":
                continue
            intent = json.loads(path.read_text(encoding="utf-8"))
            result = resolver.resolve(intent["id"], head="abc123")
            self.assertEqual(result["intent"], intent["id"])
            self.assertTrue(result["instruction_digest"])
            self.assertEqual(result["plan_digest"], resolver.digest(result["execution_plan"]))
            plan_ids = {item["id"] for item in result["execution_plan"]["checks"]}
            self.assertTrue(set(intent["certification"]["required"]).issubset(plan_ids))

    def test_resolution_is_deterministic_and_head_changes_execution_key_only(self):
        resolver = load_script("resolve_intent")
        one = resolver.resolve("library-maintenance", head="head-one")
        repeat = resolver.resolve("library-maintenance", head="head-one")
        two = resolver.resolve("library-maintenance", head="head-two")
        self.assertEqual(one["instruction_digest"], repeat["instruction_digest"])
        self.assertEqual(one["plan_digest"], repeat["plan_digest"])
        self.assertEqual(one["execution_key"], repeat["execution_key"])
        self.assertEqual(one["instruction_digest"], two["instruction_digest"])
        self.assertEqual(one["plan_digest"], two["plan_digest"])
        self.assertNotEqual(one["execution_key"], two["execution_key"])

    def test_plan_digest_changes_when_executable_meaning_changes(self):
        resolver = load_script("resolve_intent")
        registry = json.loads((ROOT / "checks" / "registry.json").read_text(encoding="utf-8"))
        certification = {"required": ["instruction-library-contract"], "optional": []}
        original = resolver.resolve_check_plan(certification, registry)
        changed_registry = copy.deepcopy(registry)
        changed_registry["checks"][0]["executor"]["argv"].append("--failfast")
        changed = resolver.resolve_check_plan(certification, changed_registry)
        self.assertNotEqual(resolver.digest(original), resolver.digest(changed))

    def test_unknown_required_check_fails_closed(self):
        resolver = load_script("resolve_intent")
        registry = json.loads((ROOT / "checks" / "registry.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "unknown certification check"):
            resolver.resolve_check_plan({"required": ["not-registered"], "optional": []}, registry)

    def test_runtime_validation_matches_schema_level_constraints(self):
        resolver = load_script("resolve_intent")
        catalog = resolver.load_json(ROOT / "instructions" / "catalog.json")
        catalog_by_id = resolver.validate_catalog(catalog)
        intent = resolver.load_json(ROOT / "intents" / "library-maintenance.json")

        invalid_id = copy.deepcopy(intent)
        invalid_id["id"] = "Bad Intent"
        with self.assertRaisesRegex(ValueError, "intent id"):
            resolver.validate_intent(invalid_id, catalog_by_id)

        duplicate_check = copy.deepcopy(intent)
        duplicate_check["certification"]["required"] = ["instruction-library-contract", "instruction-library-contract"]
        with self.assertRaisesRegex(ValueError, "unique"):
            resolver.validate_intent(duplicate_check, catalog_by_id)

    def test_executor_continues_independent_checks_and_skips_dependents(self):
        runner = load_script("run_intent_ci")
        plan = {
            "registry_version": 1,
            "declared": {"required": ["fails", "independent", "dependent"], "optional": []},
            "checks": [
                {
                    "id": "fails", "required": True, "depends_on": [], "stage": "convergence",
                    "capsule_label": "fails",
                    "executor": {"kind": "command", "argv": [sys.executable, "-c", "raise AssertionError('boom')"]},
                },
                {
                    "id": "independent", "required": True, "depends_on": [], "stage": "convergence",
                    "capsule_label": "independent",
                    "executor": {"kind": "command", "argv": [sys.executable, "-c", "print('ok')"]},
                },
                {
                    "id": "dependent", "required": True, "depends_on": ["fails"], "stage": "convergence",
                    "capsule_label": "dependent",
                    "executor": {"kind": "command", "argv": [sys.executable, "-c", "print('should not run')"]},
                },
            ],
        }
        resolved = {
            "execution_plan": plan,
            "plan_digest": runner.digest(plan),
            "failure_policy": {
                "independent_checks_continue": True,
                "dependent_checks_stop": True,
                "always_publish_capsule": True,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.execute_plan(resolved, Path(tmp))
        statuses = {item["id"]: item["status"] for item in result["checks"]}
        self.assertEqual(statuses, {"fails": "FAIL", "independent": "PASS", "dependent": "SKIP"})
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failing_check"], "fails")

    def test_capsule_prefers_causal_error_over_generic_suite_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "verify.log"
            log.write_text(
                "FAIL: test_resolve (tests.Contract)\n"
                "Traceback (most recent call last):\n"
                "AssertionError: missing module id\n"
                "FAILED (failures=1)\n",
                encoding="utf-8",
            )
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
            self.assertIn("AssertionError: missing module id", visible[0])
            self.assertNotIn("FAILED (failures=1)", visible[0])
            self.assertLessEqual(len(visible[0]), 260)


if __name__ == "__main__":
    unittest.main()
