from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class PagesWorkflowSecurityTests(unittest.TestCase):
    def test_actions_and_build_dependencies_are_immutable_and_permissions_scoped(self) -> None:
        source = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        workflow = yaml.safe_load(source)
        build = workflow["jobs"]["build"]
        deploy = workflow["jobs"]["deploy"]
        self.assertEqual(build["permissions"], {"contents": "read"})
        self.assertEqual(deploy["permissions"], {"pages": "write", "id-token": "write"})
        self.assertEqual(deploy["if"], "github.event_name == 'push'")

        references = [
            step["uses"]
            for job in (build, deploy)
            for step in job["steps"]
            if "uses" in step
        ]
        self.assertEqual(len(references), 4)
        for reference in references:
            self.assertRegex(reference, r"^[\w-]+/[\w-]+@[0-9a-f]{40}$")
        checkout = build["steps"][0]
        self.assertIs(checkout["with"]["persist-credentials"], False)
        self.assertIn("--require-hashes -r requirements-docs.lock", source)
        self.assertIn("python scripts/harden_site.py", source)

    def test_every_locked_package_has_a_full_wheel_hash(self) -> None:
        lock = (ROOT / "requirements-docs.lock").read_text(encoding="utf-8")
        rows = [line for line in lock.splitlines() if line and not line.startswith("#")]
        packages = [line for line in rows if not line.startswith(" ")]
        hashes = [line for line in rows if line.startswith(" ")]
        self.assertGreaterEqual(len(packages), 20)
        self.assertTrue(all(re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.-]+ \\?", row) for row in packages))
        self.assertGreaterEqual(len(hashes), len(packages))
        self.assertTrue(all(re.fullmatch(r"    --hash=sha256:[0-9a-f]{64} ?\\?", row) for row in hashes))


if __name__ == "__main__":
    unittest.main()
