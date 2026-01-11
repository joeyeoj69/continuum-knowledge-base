# Configuration

`kernel-tooling` is configured per downstream repository.

## File locations

- `kernel-tooling.json` (preferred; no external runtime dependencies)
- `kernel-tooling.yaml` / `kernel-tooling.yml` (optional; requires PyYAML)

You can override the location with `KERNEL_TOOLING_CONFIG`.

## Schema (v1)

Required:
- `schema_version` (integer): currently `1`.

Optional:
- `env` (object): environment variables merged into each task run.
- `ci.tasks` (object): mapping task name -> list of shell commands.

### Example

```json
{
  "schema_version": 1,
  "env": {
    "CI": "1"
  },
  "ci": {
    "tasks": {
      "lint": ["make lint"],
      "test": ["make test"],
      "build": ["make build"],
      "release": ["./scripts/release.sh --non-interactive"]
    }
  }
}
```

## Task execution model

- Each task is an ordered list of commands.
- Each command executes via `bash -lc "<command>"`.
- The task fails fast on the first non-zero exit code.

## Exit codes

- `0`: success
- `1`: a command returned non-zero
- `2`: configuration/usage error
