from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class KernelToolingConfig:
    schema_version: int
    ci_tasks: Dict[str, List[str]]
    env: Dict[str, str]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "KernelToolingConfig":
        # Minimal contract validation (MVP). Avoid external deps.
        if not isinstance(d, dict):
            raise ConfigError("Config root must be a JSON/YAML object.")

        sv = d.get("schema_version")
        if not isinstance(sv, int):
            raise ConfigError("Missing or invalid `schema_version` (expected integer).")

        ci = d.get("ci", {})
        if ci is None:
            ci = {}
        if not isinstance(ci, dict):
            raise ConfigError("`ci` must be an object.")

        tasks = ci.get("tasks", {})
        if tasks is None:
            tasks = {}
        if not isinstance(tasks, dict):
            raise ConfigError("`ci.tasks` must be an object mapping task name -> list of commands.")

        ci_tasks: Dict[str, List[str]] = {}
        for name, cmds in tasks.items():
            if not isinstance(name, str) or not name.strip():
                raise ConfigError("`ci.tasks` keys must be non-empty strings.")
            if not isinstance(cmds, list) or not all(isinstance(c, str) and c.strip() for c in cmds):
                raise ConfigError(f"`ci.tasks.{name}` must be a list of non-empty strings (shell commands).")

            ci_tasks[name] = cmds

        env = d.get("env", {})
        if env is None:
            env = {}
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            raise ConfigError("`env` must be an object mapping string->string.")

        return KernelToolingConfig(schema_version=sv, ci_tasks=ci_tasks, env=env)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}") from e


def _load_yaml(path: Path) -> Dict[str, Any]:
    # YAML support is optional to keep runtime dependency-free.
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise ConfigError(
            "YAML config requires PyYAML (pip install pyyaml), or use kernel-tooling.json instead."
        ) from e

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError("YAML config root must be an object.")
    return data


def load_config(path: Path) -> KernelToolingConfig:
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")

    if path.suffix.lower() in [".yaml", ".yml"]:
        data = _load_yaml(path)
    else:
        data = _load_json(path)

    return KernelToolingConfig.from_dict(data)


def default_config_template() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "env": {},
        "ci": {
            "tasks": {
                "lint": ["make lint"],
                "test": ["make test"],
                "build": ["make build"],
            }
        },
    }
