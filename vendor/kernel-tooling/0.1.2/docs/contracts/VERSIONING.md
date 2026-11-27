# Versioning and support policy

## Version scheme

- Pre-`v1.0.0`: SemVer *intended*, but changes may be breaking.
- `v1.0.0` and later: strict SemVer.

## Support window (recommended)

- Supported: latest minor (`vX.Y.*`) and previous minor (`vX.(Y-1).*`).
- Security fixes: backported to supported minors when feasible.

## Breaking changes

- Require a major bump (`vX+1.0.0`).
- Must ship a migration guide under `docs/migration/`.
