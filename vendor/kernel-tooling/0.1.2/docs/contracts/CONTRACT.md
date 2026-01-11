# kernel-tooling contract

This document defines what downstream repositories may depend on.

## Stable paths (public contract)

Downstream repositories may depend on the following **paths and behaviors**:

- `tools/ci/kt-ci` — CI entrypoint
  - Usage: `tools/ci/kt-ci <task> [flags]`
  - Exit codes:
    - `0` success
    - `1` task failed (command returned non-zero)
    - `2` configuration / usage error

- `tools/cli/bin/kt` — CLI entrypoint (local developer workflows)
  - Usage: `tools/cli/bin/kt <command> [flags]`
  - Same exit-code conventions as above.

- `VERSION` — the kernel-tooling version string shipped to consumers.

- `docs/contracts/*` — contract documentation and schema.

Everything else is internal and may change at any time.

## Configuration contract

`kernel-tooling` reads configuration from one of:

- `kernel-tooling.json` (preferred for MVP; dependency-free)
- `kernel-tooling.yaml` / `kernel-tooling.yml` (optional; requires `PyYAML`)

Config is detected relative to the *workspace root* (best-effort: `git rev-parse --show-toplevel`).

### Minimal schema (MVP)

```json
{
  "schema_version": 1,
  "env": {
    "EXAMPLE": "value"
  },
  "ci": {
    "tasks": {
      "lint": ["make lint"],
      "test": ["make test"],
      "build": ["make build"]
    }
  }
}
```

- `schema_version` is required and allows future migrations.
- `env` entries are added to the environment for all task commands.
- `ci.tasks.<name>` is an ordered list of shell commands executed with `bash -lc`.

See `docs/contracts/CONFIG.md` and `docs/contracts/config.schema.json`.

## Compatibility policy (starting at v1.0.0)

### Breaking changes (require major bump)

- Removing or renaming stable entrypoints (`tools/ci/kt-ci`, `tools/cli/bin/kt`)
- Incompatible changes to config schema without a supported migration path
- Changing default behavior in a way that causes previously-passing tasks to fail

### Non-breaking changes (minor/patch)

- Adding new tasks, flags, or config fields (optional)
- Bug fixes that preserve contract
- Documentation updates

### Deprecations

- Deprecations must warn for at least one minor version before removal.
- Warnings should include:
  - what will change,
  - the first version where removal happens,
  - exact migration steps.
