"""Configuration loader for spindle scripts."""

import json
import sys
from pathlib import Path
from typing import Optional

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ConfigSource:
    YAML = "spindle.yaml"
    JSON = "spindle.json"
    PYPROJECT = "pyproject.toml ([tool.spindle.scripts])"


def load_scripts(cwd: Optional[Path] = None) -> Optional[tuple[dict[str, str], str]]:
    """Load scripts configuration from spindle.yaml, spindle.json, or pyproject.toml.
    
    Returns a tuple of (scripts dict, source name) or None if no config found.
    """
    if cwd is None:
        cwd = Path.cwd()

    # 1) spindle.yaml
    yaml_path = cwd / "spindle.yaml"
    if yaml_path.exists():
        scripts = _load_from_yaml(yaml_path)
        if scripts:
            return scripts, ConfigSource.YAML

    # 2) spindle.json
    json_path = cwd / "spindle.json"
    if json_path.exists():
        scripts = _load_from_json(json_path)
        if scripts:
            return scripts, ConfigSource.JSON

    # 3) pyproject.toml -> [tool.spindle.scripts]
    toml_path = cwd / "pyproject.toml"
    if toml_path.exists():
        scripts = _load_from_pyproject(toml_path)
        if scripts:
            return scripts, ConfigSource.PYPROJECT

    return None


def _load_from_yaml(path: Path) -> Optional[dict[str, str]]:
    """Load scripts from spindle.yaml."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "scripts" in data:
            scripts = data["scripts"]
            if isinstance(scripts, dict):
                return {k: str(v) for k, v in scripts.items()}
    except Exception:
        pass
    return None


def _load_from_json(path: Path) -> Optional[dict[str, str]]:
    """Load scripts from spindle.json."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "scripts" in data:
            scripts = data["scripts"]
            if isinstance(scripts, dict):
                return {k: str(v) for k, v in scripts.items()}
    except Exception:
        pass
    return None


def _load_from_pyproject(path: Path) -> Optional[dict[str, str]]:
    """Load scripts from pyproject.toml [tool.spindle.scripts]."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        scripts = data.get("tool", {}).get("spindle", {}).get("scripts", {})
        if isinstance(scripts, dict):
            return {k: str(v) for k, v in scripts.items()}
    except Exception:
        pass
    return None
