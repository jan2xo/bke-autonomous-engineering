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


class ConsumerContractTests(unittest.TestCase):
    def build_consumer(self, root, source_ref="a" * 40):
        root = Path(root)
        (root / ".bke" / "instructions").mkdir(parents=True)
        (root / ".bke" / "checks").mkdir(parents=True)
        (root / "product.txt").write_text("ok", encoding="utf-8")
        (root / ".bke" / "instructions" / "product.md").write_text(
            "# Product Contract\n\nRepository-specific engineering constraints.\n",
            encoding="utf-8",
        )
        (root / ".bke" / "instructions" / "catalog.json").write_text(
            json.dumps({
                "version": 1,
                "modules": [
                    {"id": "repo.product-contract", "path": ".bke/instructions/product.md"}
                ],
            }),
            encoding="utf-8",
        )
        (root / ".bke" / "checks" / "registry.json").write_text(
            json.dumps({
                "version": 1,
                "checks": [
                    {
                        "id": "repo.unit",
                        "depends_on": [],
                        "executor": {
                            "kind": "command",
                            "argv": [
                                sys.executable,
                                "-c",
                                "from pathlib import Path; assert Path('product.txt').read_text() == 'ok'; print('consumer-ok')",
                            ],
                        },
                        "stage": "convergence",
                        "capsule_label": "repo.unit",
                    }
                ],
            }),
            encoding="utf-8",
        )
        (root / ".bke" / "intent.json").write_text(
            json.dumps({
                "version": 1,
                "id": "product-change",
                "instructions": ["core.github-truth", "repo.product-contract"],
                "certification": {"required": ["repo.unit"], "optional": []},
                "failure_policy": {
                    "independent_checks_continue": True,
                    "dependent_checks_stop": True,
                    "always_publish_capsule": True,
                },
            }),
            encoding="utf-8",
        )
        (root / ".bke" / "autonomous.json").write_text(
            json.dumps({
                "version": 1,
                "instruction_source": {
                    "repo": "jan2xo/bke-autonomous-engineering",
                    "ref": source_ref,
                },
                "intent_path": ".bke/intent.json",
                "instruction_catalog_path": ".bke/instructions/catalog.json",
                "check_registry_path": ".bke/checks/registry.json",
            }),
            encoding="utf-8",
        )

    def test_consumer_resolves_shared_and_repo_layers(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            result = resolver.resolve_consumer(
                tmp,
                ".bke/autonomous.json",
                "b" * 40,
                library_head="a" * 40,
                consumer_head_actual="b" * 40,
            )
        sources = {item["id"]: item["source"] for item in result["modules"]}
        self.assertEqual(sources["core.github-truth"], "library")
        self.assertEqual(sources["repo.product-contract"], "consumer")
        checks = {item["id"]: item for item in result["execution_plan"]["checks"]}
        self.assertEqual(checks["repo.unit"]["execution_root"], "consumer")
        self.assertEqual(
            result["execution_plan"]["failure_policy"],
            result["failure_policy"],
        )
        self.assertEqual(result["source"]["ref"], "a" * 40)
        self.assertTrue(result["instruction_digest"])
        self.assertTrue(result["plan_digest"])
        self.assertTrue(result["execution_key"])

    def test_runner_executes_repo_checks_from_consumer_root(self):
        resolver = load_script("resolve_consumer")
        runner = load_script("run_intent_ci")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            result = resolver.resolve_consumer(
                tmp,
                ".bke/autonomous.json",
                "b" * 40,
                library_head="a" * 40,
                consumer_head_actual="b" * 40,
            )
            execution = runner.execute_plan(
                result,
                Path(tmp) / "logs",
                consumer_root=tmp,
            )
            self.assertEqual(execution["status"], "PASS")
            self.assertEqual(execution["checks"][0]["execution_root"], "consumer")
            self.assertIn("consumer-ok", Path(execution["checks"][0]["log"]).read_text(encoding="utf-8"))

    def test_instruction_source_mismatch_fails_closed(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            with self.assertRaisesRegex(ValueError, "instruction source mismatch"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    "b" * 40,
                    library_head="c" * 40,
                    consumer_head_actual="b" * 40,
                )

    def test_consumer_checkout_head_mismatch_fails_closed(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            with self.assertRaisesRegex(ValueError, "consumer checkout head mismatch"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    "b" * 40,
                    library_head="a" * 40,
                    consumer_head_actual="d" * 40,
                )

    def test_consumer_ids_cannot_shadow_shared_namespace(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            registry_path = Path(tmp) / ".bke" / "checks" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["checks"][0]["id"] = "instruction-library-contract"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"repo\.\* namespace"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    "b" * 40,
                    library_head="a" * 40,
                    consumer_head_actual="b" * 40,
                )

    def test_consumer_paths_cannot_escape_repository(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            manifest_path = Path(tmp) / ".bke" / "autonomous.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["intent_path"] = "../outside.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes the consumer repository"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    "b" * 40,
                    library_head="a" * 40,
                    consumer_head_actual="b" * 40,
                )

    def test_capsule_includes_pinned_source_ref_without_growing_past_two_visible_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.txt"
            log.write_text("ok\n", encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts" / "render_ci_capsule.py"),
                "--status", "PASS",
                "--check", "required-plan",
                "--intent", "product-change",
                "--head", "b" * 40,
                "--source-ref", "a" * 40,
                "--instruction-digest", "1" * 64,
                "--plan-digest", "2" * 64,
                "--run-id", "77",
                "--summary", "1/1 required checks passed",
                "--log", str(log),
            ]
            output = subprocess.check_output(command, text=True)
            visible = [line for line in output.splitlines() if not line.startswith("<!--")]
            self.assertEqual(len(visible), 2)
            self.assertIn("SRC aaaaaaaaaaaa", visible[1])


if __name__ == "__main__":
    unittest.main()
