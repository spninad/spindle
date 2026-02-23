"""Configuration loader for spindle scripts."""

import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from spindle.install import load_manifest


class ConfigSource:
    YAML = "spindle.yaml"
    JSON = "spindle.json"
    TOML = "spindle.toml"
    PYPROJECT = "pyproject.toml ([tool.spindle.scripts])"


def load_scripts(cwd: Optional[Path] = None) -> Optional[tuple[dict[str, str], str]]:
    """Load scripts configuration from spindle.yaml, spindle.json, spindle.toml, or pyproject.toml.
    
    Returns a tuple of (scripts dict, source name) or None if no config found.
    """
    if cwd is None:
        cwd = Path.cwd()

    # 1) Try unified manifest (spindle.yaml, spindle.json, spindle.toml)
    manifest = load_manifest(cwd)
    if manifest and manifest.scripts:
        # Determine source based on which file exists
        if (cwd / "spindle.yaml").exists():
            return manifest.scripts, ConfigSource.YAML
        elif (cwd / "spindle.json").exists():
            return manifest.scripts, ConfigSource.JSON
        elif (cwd / "spindle.toml").exists():
            return manifest.scripts, ConfigSource.TOML

    # 2) pyproject.toml -> [tool.spindle.scripts]
    pyproject_path = cwd / "pyproject.toml"
    if pyproject_path.exists():
        scripts = _load_from_pyproject(pyproject_path)
        if scripts:
            return scripts, ConfigSource.PYPROJECT

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
