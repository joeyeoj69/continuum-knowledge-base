# Downstream consumption

`kernel-tooling` supports two pinned consumption patterns:

## Option A — git submodule

Pros:
- Pin exact commit
- Simple local iteration for contributors

Cons:
- Submodule UX and checkout complexity

Recommended path:

```bash
git submodule add <KERNEL_TOOLING_REPO_URL> .kernel-tooling
git commit -m "Add kernel-tooling submodule"
```

Downstream can call tooling directly:

```bash
./.kernel-tooling/tools/ci/kt-ci lint
./.kernel-tooling/tools/cli/bin/kt doctor
```

Or create thin wrappers:

```bash
./.kernel-tooling/tools/cli/bin/kt init
```

(This writes `tools/ci/kt-ci` and `tools/cli/kt` wrappers if missing.)

## Option B — vendored, versioned release

Pros:
- No submodule workflow
- Easy to sign and attest artifacts

Cons:
- Requires release automation
- Needs an update script

Recommended layout:

```
vendor/
  kernel-tooling/
    v1.2.3/
      (extracted release tarball contents)
    current -> v1.2.3   (symlink or copied directory)
```

Downstream wrapper scripts should point to `vendor/kernel-tooling/current/...` to make upgrades a one-line change.

## Rollback

- Submodule: `git checkout <previous-sha> -- .kernel-tooling` then commit.
- Vendor: repoint `current` to the previous version directory (or re-extract prior tarball).
