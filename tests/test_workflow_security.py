from __future__ import annotations

import re
import subprocess
import tempfile
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
        self.assertEqual(build["runs-on"], "ubuntu-24.04")
        self.assertEqual(deploy["runs-on"], "ubuntu-24.04")
        self.assertEqual(build["permissions"], {"contents": "read"})
        self.assertEqual(deploy["permissions"], {"pages": "write", "id-token": "write"})
        self.assertEqual(deploy["if"], "github.event_name == 'push'")

        references = [
            step["uses"]
            for job in (build, deploy)
            for step in job["steps"]
            if "uses" in step
        ]
        self.assertEqual(
            references,
            [
                "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
                "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa",
                "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e",
            ],
        )
        checkout = build["steps"][0]
        self.assertIs(checkout["with"]["persist-credentials"], False)
        setup_python = build["steps"][1]
        self.assertEqual(setup_python["with"]["python-version"], "3.11.18")
        self.assertIn("--require-hashes -r requirements-docs.lock", source)
        self.assertIn("python scripts/harden_site.py", source)
        self.assertIn("bash scripts/check_generated_site.sh", source)

    def test_build_is_an_always_run_pull_request_gate(self) -> None:
        source = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        workflow = yaml.load(source, Loader=yaml.BaseLoader)
        triggers = workflow["on"]
        self.assertIn("pull_request", triggers)
        self.assertFalse(triggers["pull_request"])
        self.assertNotIn("paths:", source)

    def test_deploy_example_has_byte_stable_shell_highlighting(self) -> None:
        checklist = (ROOT / "docs/ops/kb-deploy-checklist.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "echo >> docs/index.md\n"
            "  git add docs/index.md\n"
            "  git commit -m chore-trigger-pages-deploy\n"
            "  git push",
            checklist,
        )
        self.assertNotIn('echo "" >> docs/index.md', checklist)
        self.assertNotIn('git commit -m "chore: trigger pages deploy"', checklist)

    def test_generated_site_guard_rejects_tracked_and_untracked_output(self) -> None:
        guard = ROOT / "scripts/check_generated_site.sh"
        source = guard.read_text(encoding="utf-8")
        self.assertIn("git diff --exit-code -- site", source)
        self.assertIn("git ls-files --others -z -- site", source)
        self.assertNotIn("--exclude-standard", source)

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            site = repo / "site"
            site.mkdir()
            tracked = site / "tracked.txt"
            tracked.write_text("reviewed\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "add", "site/tracked.txt"], cwd=repo, check=True)

            clean = subprocess.run(
                ["bash", str(guard)], cwd=repo, text=True, capture_output=True
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)

            untracked = site / "unreviewed.js"
            untracked.write_text("alert(1)\n", encoding="utf-8")
            rejected = subprocess.run(
                ["bash", str(guard)], cwd=repo, text=True, capture_output=True
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("untracked generated site files", rejected.stderr)
            untracked.unlink()

            (repo / ".gitignore").write_text("site/ignored.js\n", encoding="utf-8")
            ignored = site / "ignored.js"
            ignored.write_text("alert(2)\n", encoding="utf-8")
            rejected = subprocess.run(
                ["bash", str(guard)], cwd=repo, text=True, capture_output=True
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("site/ignored.js", rejected.stderr)
            ignored.unlink()

            tracked.write_text("changed\n", encoding="utf-8")
            rejected = subprocess.run(
                ["bash", str(guard)], cwd=repo, text=True, capture_output=True
            )
            self.assertNotEqual(rejected.returncode, 0)

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
