#!/usr/bin/env python3
"""Fail closed if a generated Pages artifact can load mutable browser code."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path


MERMAID_FALLBACK = b'wt("https://unpkg.com/mermaid@11/dist/mermaid.min.js")'
INERT_FALLBACK = b'wt("data:,")'
RESIZE_FALLBACK = b'typeof ResizeObserver=="undefined"?wt("https://unpkg.com/resize-observer-polyfill"):I(void 0)'
RESIZE_INERT = b'I(void 0)'
RESIZE_CTOR = b'new ResizeObserver('
RESIZE_SAFE_CTOR = b'new (typeof ResizeObserver=="undefined"?class{observe(){}unobserve(){}disconnect(){}}:ResizeObserver)('
TEXT_SUFFIXES = {".html", ".js", ".mjs", ".json", ".css"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RAW_HTML = re.compile(r"<\s*(?:!--|[!?/]?[A-Za-z])")
SCRIPT_BUNDLE = re.compile(r"^(?:\.\./)*assets/javascripts/bundle\.[0-9a-f]+\.min\.js$")

# Three executable inline scripts are emitted by the hash-locked Material
# 9.6.18 theme. The scope script has four path-depth variants. A dependency
# upgrade must be reviewed and this list changed deliberately.
TRUSTED_SCOPE_SHA256 = frozenset({
    "6a9a103c779f08d5a3c5b0a6f87cd50ce016e024955a163b5729508e0385c9f9",
    "7b1a915eb5bfd256a22260ab4c4f1aef4bf1cb2635d05255229a72b4b7ff75b6",
    "fcaf69d89b44a82c9c2f67d26c4a2731a924b5e5a9007bf9ef1db09dd2ea30da",
    "fe7866f29e74289c6fc162e0830275385f1782ae56fdbde22840884cb0127ce8",
})
TRUSTED_PALETTE_SHA256 = "0eb10c249dbdb0beef225a10ce5cbe55418cc4a7014cc208f8e7d6ed8f00906e"
TRUSTED_TABS_SHA256 = "ffcc0f7735fdab434d257c80e65cec2e88d716991e69757185b7e450e41a5b2f"


def reject_raw_html(path: Path) -> None:
    """This site has no authored HTML; require Markdown syntax for new content."""
    fence_char = ""
    fence_size = 0
    inline_size = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = FENCE.match(line)
        if fence_char:
            if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_size and not line[match.end():].strip():
                fence_char = ""
            continue
        if match and not inline_size:
            fence_char, fence_size = match.group(1)[0], len(match.group(1))
            if line[match.end():].strip().lower().startswith("mermaid"):
                raise ValueError(f"Mermaid source block requires a reviewed static replacement: {path}:{number}")
            continue
        visible: list[str] = []
        index = 0
        while index < len(line):
            if line[index] == "`":
                end = index + 1
                while end < len(line) and line[end] == "`":
                    end += 1
                size = end - index
                if not inline_size:
                    inline_size = size
                elif inline_size == size:
                    inline_size = 0
                visible.extend(" " * size)
                index = end
            else:
                visible.append(" " if inline_size else line[index])
                index += 1
        text = "".join(visible)
        for candidate in RAW_HTML.finditer(text):
            backslashes = len(text[:candidate.start()]) - len(text[:candidate.start()].rstrip("\\"))
            if backslashes % 2 == 0:
                raise ValueError(f"raw HTML is not allowed in Markdown: {path}:{number}")
    if fence_char or inline_size:
        raise ValueError(f"unclosed Markdown code span or fence: {path}")


class ScriptInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self.current_script: tuple[dict[str, str | None], list[str]] | None = None
        self.unsafe_markup: list[str] = []
        self.mermaid_elements = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if len(attributes) != len(attrs):
            self.unsafe_markup.append("duplicate attribute")
        if tag == "script":
            self.current_script = (attributes, [])
        if tag in {"base", "iframe", "frame", "frameset", "object", "embed", "style", "foreignobject"}:
            self.unsafe_markup.append(tag)
        if tag == "meta" and "http-equiv" in attributes:
            self.unsafe_markup.append("meta http-equiv")
        for name, value in attrs:
            if name.startswith("on") or name in {"srcdoc", "formaction"}:
                self.unsafe_markup.append(name)
            if value and name in {"src", "href", "action", "xlink:href"}:
                lower = value.strip().lower()
                scheme_view = "".join(lower.split())
                if scheme_view.startswith(("javascript:", "vbscript:", "data:", "blob:")):
                    self.unsafe_markup.append(f"{name} scheme")
                if tag == "link" and lower.startswith(("https://", "http://", "//")):
                    self.unsafe_markup.append("external link")
        if "mermaid" in (attributes.get("class") or "").split():
            self.mermaid_elements += 1

    def handle_data(self, data: str) -> None:
        if self.current_script is not None:
            self.current_script[1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.current_script is not None:
            attrs, data = self.current_script
            self.scripts.append((attrs, "".join(data)))
            self.current_script = None

    def validate(self, page: Path, bundle: Path) -> None:
        if self.unsafe_markup or self.mermaid_elements or self.current_script is not None:
            raise ValueError(f"unreviewed active markup in {page}: {self.unsafe_markup}")
        if len(self.scripts) != 5:
            raise ValueError(f"unreviewed script count in {page}")
        for index, (attributes, body) in enumerate(self.scripts):
            if index in (0, 1, 2):
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                expected = (
                    TRUSTED_SCOPE_SHA256 if index == 0 else
                    {TRUSTED_PALETTE_SHA256} if index == 1 else
                    {TRUSTED_TABS_SHA256}
                )
                if attributes or digest not in expected:
                    raise ValueError(f"unreviewed inline script in {page}")
            elif index == 3:
                if attributes != {"id": "__config", "type": "application/json"}:
                    raise ValueError(f"unreviewed config script in {page}")
            else:
                src = attributes.get("src") or ""
                local_bundle = (
                    (page.parent / src).resolve() == bundle.resolve()
                    if SCRIPT_BUNDLE.fullmatch(src)
                    else page.name == "404.html" and src == f"/assets/javascripts/{bundle.name}"
                )
                if (
                    set(attributes) != {"src"}
                    or not local_bundle
                ):
                    raise ValueError(f"unreviewed script source in {page}")


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

    content = bundle.read_bytes()
    if content.count(RESIZE_FALLBACK) == 1 and content.count(RESIZE_CTOR) == 1:
        bundle.write_bytes(
            content.replace(RESIZE_FALLBACK, RESIZE_INERT).replace(RESIZE_CTOR, RESIZE_SAFE_CTOR)
        )
    elif content.count(RESIZE_FALLBACK) != 0 or content.count(RESIZE_SAFE_CTOR) != 1:
        raise ValueError("Material ResizeObserver fallback changed; review the pinned theme")

    # Source maps are not required to serve the site and retain the original
    # remote loader in copied third-party source text.
    maps = list(site.rglob("*.map"))
    for path in maps:
        path.unlink()

    # MkDocs writes the current wall-clock time into the sitemap gzip header.
    # Re-encode the same reviewed XML with fixed metadata so a locked rebuild is
    # byte-for-byte identical and the generated-site diff gate is meaningful.
    sitemap = site / "sitemap.xml"
    sitemap_gzip = site / "sitemap.xml.gz"
    if sitemap_gzip.exists():
        if not sitemap.is_file():
            raise ValueError("compressed sitemap exists without sitemap.xml")
        with sitemap_gzip.open("wb") as output:
            with gzip.GzipFile(
                filename="", mode="wb", compresslevel=9, fileobj=output, mtime=0
            ) as archive:
                archive.write(sitemap.read_bytes())

    for path in docs.rglob("*.md"):
        reject_raw_html(path)

    pages = list(site.rglob("*.html"))
    if not pages:
        raise ValueError("generated site has no HTML pages")
    for path in pages:
        inventory = ScriptInventory()
        inventory.feed(path.read_text(encoding="utf-8"))
        inventory.validate(path, bundle)

    for path in site.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            data = path.read_bytes()
            if any(remote in data for remote in (b"unpkg.com/mermaid@", b"unpkg.com/resize-observer-polyfill", b"fonts.googleapis.com", b"fonts.gstatic.com")):
                raise ValueError(f"mutable browser dependency remains in {path}")

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
