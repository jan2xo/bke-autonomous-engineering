import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_request_validator():
    path = ROOT / "scripts" / "validate_certification_request.py"
    spec = importlib.util.spec_from_file_location("validate_certification_request", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ControlPlaneRequestTests(unittest.TestCase):
    def test_request_binds_repo_head_pr_and_manifest(self):
        module = load_request_validator()
        request = module.validate_request(
            "jan2xo/bke-worker",
            "a" * 40,
            "66",
            ".bke/autonomous.json",
        )
        self.assertEqual(request["repository"], "jan2xo/bke-worker")
        self.assertEqual(request["head"], "a" * 40)
        self.assertEqual(request["pull_request"], 66)

    def test_request_rejects_other_owner_and_moving_head(self):
        module = load_request_validator()
        with self.assertRaisesRegex(ValueError, "jan2xo"):
            module.validate_request(
                "someone/bke-worker",
                "a" * 40,
                1,
                ".bke/autonomous.json",
            )
        with self.assertRaisesRegex(ValueError, "40-character"):
            module.validate_request(
                "jan2xo/bke-worker",
                "main",
                1,
                ".bke/autonomous.json",
            )

    def test_request_rejects_manifest_path_escape(self):
        module = load_request_validator()
        with self.assertRaisesRegex(ValueError, "safe relative"):
            module.validate_request(
                "jan2xo/bke-worker",
                "a" * 40,
                1,
                "../autonomous.json",
            )


if __name__ == "__main__":
    unittest.main()
