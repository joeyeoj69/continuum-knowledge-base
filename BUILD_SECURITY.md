# Pages build and browser dependency repair — 2026-11-25

This source change addresses Daybreak scan
`wfr_a39d8bbd5bd99ffb8524b2d0c5060a161ee1b3dfe111ba7d3851d180c2a8b237`
at `main@8830f514ff5810c0ad7a071ae71ad31c2ef4a37a`:

- `acf_104d29a4485ef3a8cbcb1b9204b5718b`: mutable CI actions and Python
  package resolution could alter the Pages artifact. The four official GitHub
  Actions are pinned to full commit SHAs read from their official major-version
  refs. `requirements-docs.lock` pins the complete 29-package MkDocs Material
  9.6.18 wheel closure, with PyPI wheel hashes for the Python 3.11 Linux CI
  runner and Studio1 macOS arm64. The build job has only `contents: read`;
  `pages: write` and `id-token: write` belong only to the deployment job.
  Checkout does not persist credentials.
- `acf_44bd41f3d9678e5533980d4baafc9f38`: the mutable Mermaid CDN script
  ran on every page. The three source diagrams are now readable static text or
  tables. The global CDN script and initializer are removed. After the pinned
  theme build, `scripts/harden_site.py` replaces the dormant Material fallback
  with an inert local data URL, removes source maps that retain the old URL,
  and rejects any generated HTML with an external script or Mermaid element.

The root `TODO.md` is copied into `docs/TODO.md` because the existing navigation
referenced a page outside MkDocs' `docs/` source and made `mkdocs build --strict`
fail. The site gate requires the two copies to match. The checked-in `site/`
was rebuilt from the pinned docs stack and hardened for the repository view.

Verification: the Linux and macOS wheel sets each passed an offline
`pip download --require-hashes` against the lock. An isolated macOS Python 3.11
environment installed the locked wheels, four security tests passed, and
`mkdocs build --strict` plus `python scripts/harden_site.py` produced 36 pages
with no external script tags or Mermaid loader URL. These are source and build
results. GitHub Pages deployment, live response headers/CSP, environment
protections, and Daybreak finding closure require separate provider readback.
