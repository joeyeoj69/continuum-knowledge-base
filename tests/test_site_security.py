from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.harden_site import RESIZE_SAFE_CTOR, harden_site, reject_raw_html


ROOT = Path(__file__).resolve().parents[1]


class PublishedSiteSecurityTests(unittest.TestCase):
    def make_site(self, root: Path) -> tuple[Path, Path, Path]:
        site = root / "site"
        docs = root / "docs"
        source_bundle = next((ROOT / "site/assets/javascripts").glob("bundle.*.min.js"))
        bundle = site / "assets/javascripts" / source_bundle.name
        bundle.parent.mkdir(parents=True)
        docs.mkdir()
        (docs / "index.md").write_text("# Safe page\n", encoding="utf-8")
        (site / "index.html").write_bytes((ROOT / "site/index.html").read_bytes())
        bundle.write_bytes(source_bundle.read_bytes())
        return site, docs, bundle

    def test_pinned_theme_artifact_and_reintroduced_remote_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site, docs, bundle = self.make_site(Path(directory))
            self.assertEqual(harden_site(site, docs), (1, 0))
            self.assertIn(RESIZE_SAFE_CTOR, bundle.read_bytes())
            self.assertNotIn(b"unpkg.com/resize-observer-polyfill", bundle.read_bytes())
            (site / "index.html").write_text(
                (site / "index.html").read_text() + '<script src="data:text/javascript,alert(1)"></script>',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unreviewed active markup"):
                harden_site(site, docs)

    def test_rejects_source_diagram_before_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site, docs, _ = self.make_site(Path(directory))
            (docs / "index.md").write_text("```mermaid\nflowchart LR\n```\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Mermaid source block"):
                harden_site(site, docs)

    def test_rejects_raw_html_and_generated_active_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            site, docs, _ = self.make_site(Path(directory))
            source = docs / "index.md"
            for payload in (
                '<script>alert(1)</script>',
                '<img src=x onerror="alert(1)">',
                '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
                '<base href="https://attacker.example/">',
            ):
                with self.subTest(payload=payload):
                    source.write_text("# Safe page\n" + payload + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "raw HTML"):
                        harden_site(site, docs)
            source.write_text("# Safe page\n", encoding="utf-8")
            page = site / "index.html"
            original = page.read_text(encoding="utf-8")
            for payload in (
                '<img src=x onerror="alert(1)">',
                '<iframe srcdoc="alert(1)"></iframe>',
                '<base href="https://attacker.example/">',
                '<link rel="stylesheet" href="https://attacker.example/a.css">',
                '<style>@import url(https://attacker.example/a.css)</style>',
                '<img src="safe.png" src="javascript:alert(1)">',
                '<a href="java&#9;script:alert(1)">go</a>',
            ):
                with self.subTest(payload=payload):
                    page.write_text(original + payload, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "unreviewed active markup"):
                        harden_site(site, docs)

    def test_code_spans_and_fences_are_not_raw_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "safe.md"
            path.write_text("`<script>x</script>`\n```html\n<script>x</script>\n```\n", encoding="utf-8")
            reject_raw_html(path)


if __name__ == "__main__":
    unittest.main()
