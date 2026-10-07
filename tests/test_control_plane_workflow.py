import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ControlPlaneWorkflowContractTests(unittest.TestCase):
    def test_certification_workflow_separates_trust_domains(self):
        workflow = (ROOT / ".github" / "workflows" / "consumer-certify.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: BKE Consumer Certification", workflow)
        self.assertIn("name: Trusted resolve", workflow)
        self.assertIn("name: Unprivileged execute", workflow)
        self.assertIn("name: Trusted report", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("BKE_ENGINEERING_GITHUB_APP_BROKER_URL", workflow)
        self.assertIn("bke-engineering-github-app-broker", workflow)

        execute = workflow.split("\n  execute:", 1)[1].split("\n  report:", 1)[0]
        self.assertIn("permissions: {}", execute)
        self.assertNotIn("id-token: write", execute)
        self.assertNotIn("BKE_ENGINEERING_GITHUB_APP_BROKER_URL", execute)
        self.assertNotIn("repository-token", execute)
        self.assertNotIn("bke-autonomous-engineering", execute)

        resolve = workflow.split("\n  resolve:", 1)[1].split("\n  execute:", 1)[0]
        self.assertIn("id-token: write", resolve)
        self.assertIn('"purpose": "resolve"', resolve)
        self.assertIn("--json-out handoff/resolved-intent.json", resolve)
        self.assertNotIn("--bundle-out", resolve)

        report = workflow.split("\n  report:", 1)[1]
        self.assertIn("id-token: write", report)
        self.assertIn('"purpose": "report"', report)
        self.assertIn("BKE Intent CI", report)

    def test_direct_private_action_consumer_path_is_removed(self):
        direct_action = ROOT / ".github" / "actions" / "intent-ci" / "action.yml"
        self.assertFalse(direct_action.exists())


if __name__ == "__main__":
    unittest.main()
