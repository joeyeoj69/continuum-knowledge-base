from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


class RunError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    code: int


def run_shell_commands(
    *,
    commands: Sequence[str],
    cwd: Path,
    env: Dict[str, str],
    dry_run: bool = False,
    debug: bool = False,
) -> CommandResult:
    if not commands:
        return CommandResult(code=0)

    merged_env = os.environ.copy()
    merged_env.update(env)

    for cmd in commands:
        if debug or dry_run:
            print(f"+ {cmd}")
        if dry_run:
            continue

        # Use bash -lc for consistent behavior across CI/local (macOS/Linux).
        proc = subprocess.run(
            ["bash", "-lc", cmd],
            cwd=str(cwd),
            env=merged_env,
        )
        if proc.returncode != 0:
            raise RunError(f"Command failed with exit code {proc.returncode}: {cmd}")
    return CommandResult(code=0)
