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
    def git(self, root, *args, capture=False):
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            check=True,
        )
        return completed.stdout.strip() if capture else None

    def commit_consumer(self, root, message="fixture"):
        root = Path(root)
        if not (root / ".git").exists():
            self.git(root, "init", "-q")
            self.git(root, "config", "user.email", "bke-tests@example.invalid")
            self.git(root, "config", "user.name", "BKE Tests")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", message)
        return self.git(root, "rev-parse", "HEAD", capture=True)

    def build_consumer(self, root, source_ref="a" * 40, product_text="ok"):
        root = Path(root)
        (root / ".bke" / "instructions").mkdir(parents=True)
        (root / ".bke" / "checks").mkdir(parents=True)
        (root / "product.txt").write_text(product_text, encoding="utf-8")
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
            head = self.commit_consumer(tmp)
            result = resolver.resolve_consumer(
                tmp,
                ".bke/autonomous.json",
                head,
                library_head="a" * 40,
                consumer_head_actual=head,
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
            head = self.commit_consumer(tmp)
            result = resolver.resolve_consumer(
                tmp,
                ".bke/autonomous.json",
                head,
                library_head="a" * 40,
                consumer_head_actual=head,
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
            head = self.commit_consumer(tmp)
            with self.assertRaisesRegex(ValueError, "instruction source mismatch"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    head,
                    library_head="c" * 40,
                    consumer_head_actual=head,
                )

    def test_consumer_checkout_head_mismatch_fails_closed(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            head = self.commit_consumer(tmp)
            with self.assertRaisesRegex(ValueError, "consumer checkout head mismatch"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    "d" * 40,
                    library_head="a" * 40,
                    consumer_head_actual=head,
                )

    def test_consumer_ids_cannot_shadow_shared_namespace(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            registry_path = Path(tmp) / ".bke" / "checks" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["checks"][0]["id"] = "instruction-library-contract"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            head = self.commit_consumer(tmp, "invalid namespace")
            with self.assertRaisesRegex(ValueError, "consumer check ids"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    head,
                    library_head="a" * 40,
                    consumer_head_actual=head,
                )

    def test_consumer_paths_cannot_escape_repository(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            self.build_consumer(tmp)
            manifest_path = Path(tmp) / ".bke" / "autonomous.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["intent_path"] = "../outside.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            head = self.commit_consumer(tmp, "invalid path")
            with self.assertRaisesRegex(ValueError, "escapes the consumer repository"):
                resolver.resolve_consumer(
                    tmp,
                    ".bke/autonomous.json",
                    head,
                    library_head="a" * 40,
                    consumer_head_actual=head,
                )


    def test_dirty_tracked_content_is_rejected_before_resolution_including_staged_changes(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_consumer(root)
            head = self.commit_consumer(root)
            (root / "product.txt").write_text("dirty", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "consumer resolution tracked files differ from HEAD"):
                resolver.resolve_consumer(
                    root,
                    ".bke/autonomous.json",
                    head,
                    library_head="a" * 40,
                    consumer_head_actual=head,
                )

            self.git(root, "add", "product.txt")
            with self.assertRaisesRegex(ValueError, "consumer resolution tracked files differ from HEAD"):
                resolver.resolve_consumer(
                    root,
                    ".bke/autonomous.json",
                    head,
                    library_head="a" * 40,
                    consumer_head_actual=head,
                )

    def test_dirty_tracked_content_after_resolution_cannot_turn_failure_into_pass(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_consumer(root, product_text="bad")
            head = self.commit_consumer(root)
            resolved = resolver.resolve_consumer(
                root,
                ".bke/autonomous.json",
                head,
                library_head="a" * 40,
                consumer_head_actual=head,
            )
            resolved_path = root / ".bke-resolved.json"
            result_path = root / ".bke-result.json"
            resolved_path.write_text(
                json.dumps({key: value for key, value in resolved.items() if key != "bundle"}),
                encoding="utf-8",
            )
            (root / "product.txt").write_text("ok", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_intent_ci.py"),
                    "--resolved", str(resolved_path),
                    "--result-out", str(result_path),
                    "--log-dir", str(root / ".bke-logs"),
                    "--consumer-root", str(root),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("consumer execution tracked files differ from HEAD", completed.stdout)
            self.assertFalse(result_path.exists())

    def test_generated_untracked_evidence_does_not_make_consumer_dirty(self):
        resolver = load_script("resolve_consumer")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_consumer(root)
            head = self.commit_consumer(root)
            evidence = root / ".bke-ci"
            evidence.mkdir()
            (evidence / "generated.txt").write_text("evidence", encoding="utf-8")
            result = resolver.resolve_consumer(
                root,
                ".bke/autonomous.json",
                head,
                library_head="a" * 40,
                consumer_head_actual=head,
            )
            self.assertEqual(result["head"], head)

    def test_consumer_namespace_runtime_matches_published_schema_pattern(self):
        resolver = load_script("resolve_consumer")
        core = resolver.load_core()
        valid_catalog = {
            "version": 1,
            "modules": [{"id": "repo.a", "path": ".bke/instructions/product.md"}],
        }
        self.assertIn("repo.a", resolver.validate_consumer_catalog(valid_catalog, core))

        for invalid_id in ("repo.", "repo.-x", "repo..x"):
            bad_catalog = {
                "version": 1,
                "modules": [{"id": invalid_id, "path": ".bke/instructions/product.md"}],
            }
            with self.assertRaisesRegex(ValueError, r"repo\.\* namespace"):
                resolver.validate_consumer_catalog(bad_catalog, core)

            bad_registry = {
                "version": 1,
                "checks": [{
                    "id": invalid_id,
                    "depends_on": [],
                    "executor": {"kind": "command", "argv": [sys.executable, "-c", "pass"]},
                    "stage": "convergence",
                    "capsule_label": "bad",
                }],
            }
            with self.assertRaisesRegex(ValueError, "consumer check ids must match"):
                resolver.validate_consumer_registry_shape(bad_registry)

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
