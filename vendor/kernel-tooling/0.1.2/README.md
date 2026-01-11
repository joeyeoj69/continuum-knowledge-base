# kernel-tooling

Canonical, versioned CI + CLI tooling consumed by downstream ops repositories (e.g., SRF / Continuum / Template)
via **git submodule** or **vendored, versioned releases**.

## What this repository provides

- `tools/ci/*`: CI orchestration entrypoints and helpers (provider-agnostic; invoke from GitHub Actions, Buildkite, etc.)
- `tools/cli/*`: Developer-facing CLI entrypoints for local workflows and repo scaffolding
- `docs/contracts/*`: Stability guarantees and configuration schema

## Public contract (stable)

Downstream repos may rely on:

- `tools/ci/kt-ci` (CI entrypoint)
- `tools/cli/bin/kt` (CLI entrypoint)
- `VERSION`
- `docs/contracts/*`

Everything else is **internal** and may change without notice.

## Quickstart (downstream)

### Option A — git submodule (recommended for early adoption)

```bash
git submodule add <KERNEL_TOOLING_REPO_URL> .kernel-tooling
git commit -m "Add kernel-tooling submodule"
```

Add wrappers (or call entrypoints directly in CI):

```bash
./.kernel-tooling/tools/ci/kt-ci lint
./.kernel-tooling/tools/cli/bin/kt doctor
```

### Option B — vendored release (recommended for broad consumption)

- Download a tagged release tarball and extract to `vendor/kernel-tooling/<version>/`
- Point wrappers to the pinned version directory.

See: `docs/contracts/CONSUMPTION.md`

## Development

```bash
make test
```

## License

See `LICENSE`.
