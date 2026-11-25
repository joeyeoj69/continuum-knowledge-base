#!/usr/bin/env python3
"""Fail closed if a generated Pages artifact can load mutable browser code."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path


MERMAID_FALLBACK = b'wt("https://unpkg.com/mermaid@11/dist/mermaid.min.js")'
INERT_FALLBACK = b'wt("data:,")'
TEXT_SUFFIXES = {".html", ".js", ".mjs", ".json", ".css"}


class ScriptInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.external_scripts: list[str] = []
        self.mermaid_elements = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script":
            src = (attributes.get("src") or "").strip().lower()
            if src.startswith(("https://", "http://", "//")):
                self.external_scripts.append(src)
        if "mermaid" in (attributes.get("class") or "").split():
            self.mermaid_elements += 1


def harden_site(site: Path, docs: Path) -> tuple[int, int]:
    if not site.is_dir() or not docs.is_dir():
        raise ValueError("site and docs directories are required")

    root_todo = docs.parent / "TODO.md"
    published_todo = docs / "TODO.md"
    if root_todo.exists() and (
        not published_todo.exists() or root_todo.read_bytes() != published_todo.read_bytes()
    ):
        raise ValueError("root and published TODO.md copies differ")

    # Material 9.6.18 has an automatic remote Mermaid fallback. There are no
    # diagram blocks after the source conversion, but remove this dormant URL
    # as well so a later theme change cannot silently restore the trust path.
    bundles = list(site.glob("assets/javascripts/bundle.*.min.js"))
    if len(bundles) != 1:
        raise ValueError("expected exactly one Material JavaScript bundle")
    bundle = bundles[0]
    content = bundle.read_bytes()
    if content.count(MERMAID_FALLBACK) == 1:
        bundle.write_bytes(content.replace(MERMAID_FALLBACK, INERT_FALLBACK))
    elif content.count(INERT_FALLBACK) != 1:
        raise ValueError("Material Mermaid fallback changed; review the pinned theme")

    # Source maps are not required to serve the site and retain the original
    # remote loader in copied third-party source text.
    maps = list(site.rglob("*.map"))
    for path in maps:
        path.unlink()

    for path in docs.rglob("*.md"):
        if any(line.lstrip().startswith("```mermaid") for line in path.read_text(encoding="utf-8").splitlines()):
            raise ValueError(f"Mermaid source block requires a reviewed static replacement: {path}")

    pages = list(site.rglob("*.html"))
    if not pages:
        raise ValueError("generated site has no HTML pages")
    for path in pages:
        inventory = ScriptInventory()
        inventory.feed(path.read_text(encoding="utf-8"))
        if inventory.external_scripts or inventory.mermaid_elements:
            raise ValueError(f"unreviewed script or Mermaid element in {path}")

    for path in site.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            if b"unpkg.com/mermaid@" in path.read_bytes():
                raise ValueError(f"mutable Mermaid loader remains in {path}")

    return len(pages), len(maps)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    args = parser.parse_args()
    try:
        pages, maps = harden_site(args.site, args.docs)
    except ValueError as exc:
        parser.exit(1, f"site security check failed: {exc}\n")
    print(f"SITE_SECURITY_OK pages={pages} source_maps_removed={maps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
