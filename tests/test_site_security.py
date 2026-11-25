from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.harden_site import MERMAID_FALLBACK, harden_site


class PublishedSiteSecurityTests(unittest.TestCase):
    def make_site(self, root: Path) -> tuple[Path, Path, Path]:
        site = root / "site"
        docs = root / "docs"
        bundle = site / "assets/javascripts/bundle.example.min.js"
        bundle.parent.mkdir(parents=True)
        docs.mkdir()
        (docs / "index.md").write_text("# Safe page\n", encoding="utf-8")
        (site / "index.html").write_text(
            '<html><script src="assets/javascripts/bundle.example.min.js"></script></html>',
            encoding="utf-8",
        )
        bundle.write_bytes(MERMAID_FALLBACK)
        return site, docs, bundle

    def test_replaces_material_fallback_and_rejects_reintroduced_remote_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site, docs, bundle = self.make_site(Path(directory))
            self.assertEqual(harden_site(site, docs), (1, 0))
            self.assertNotIn(MERMAID_FALLBACK, bundle.read_bytes())
            (site / "index.html").write_text(
                '<script src=" HTTPS://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unreviewed script"):
                harden_site(site, docs)

    def test_rejects_source_diagram_before_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site, docs, _ = self.make_site(Path(directory))
            (docs / "index.md").write_text("```mermaid\nflowchart LR\n```\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Mermaid source block"):
                harden_site(site, docs)


if __name__ == "__main__":
    unittest.main()
