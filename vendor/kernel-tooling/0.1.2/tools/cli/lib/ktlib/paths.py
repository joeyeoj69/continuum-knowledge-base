from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional


def kernel_tooling_root() -> Path:
    """Return the root directory of the kernel-tooling repository.

    Assumes this file lives at: <root>/tools/cli/lib/ktlib/paths.py
    """
    return Path(__file__).resolve().parents[4]


def _git_toplevel(start: Path) -> Optional[Path]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            return Path(out)
    except Exception:
        return None
    return None


def workspace_root(start: Optional[Path] = None) -> Path:
    """Best-effort workspace (downstream repo) root detection."""
    start = (start or Path.cwd()).resolve()

    # Prefer git if available.
    git_root = _git_toplevel(start)
    if git_root is not None:
        return git_root

    # Fallback: walk up for a .git directory.
    cur = start
    for _ in range(50):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    # Last resort: current directory.
    return start


def default_config_paths(workspace: Path) -> list[Path]:
    """Ordered list of supported config locations."""
    return [
        workspace / "kernel-tooling.json",
        workspace / "kernel-tooling.yaml",
        workspace / "kernel-tooling.yml",
    ]


def find_config_path(workspace: Path) -> Optional[Path]:
    env = os.environ.get("KERNEL_TOOLING_CONFIG")
    if env:
        p = (workspace / env).resolve() if not Path(env).is_absolute() else Path(env).resolve()
        return p

    for p in default_config_paths(workspace):
        if p.exists():
            return p
    return None
