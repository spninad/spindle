"""Component installation logic for spindle."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

import requests
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class ComponentIdentifier:
    """Parsed component identifier (user/repo/path)."""
    user: str
    repo: str
    path: str

    @classmethod
    def parse(cls, identifier: str) -> Optional["ComponentIdentifier"]:
        """Parse a component identifier string."""
        parts = identifier.split("/", 2)
        if len(parts) < 2:
            return None
        user = parts[0]
        repo = parts[1]
        path = parts[2] if len(parts) > 2 else "*"
        return cls(user=user, repo=repo, path=path)


@dataclass
class ComponentDefinition:
    """A component definition from the manifest."""
    files: list[str]
    dependencies: list[str]


@dataclass
class SpindleManifest:
    """The spindle manifest (from YAML, JSON, or TOML)."""
    name: str
    components: dict[str, ComponentDefinition] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SpindleManifest":
        """Parse manifest from a dictionary."""
        components = {}
        for name, comp_data in data.get("components", {}).items():
            components[name] = ComponentDefinition(
                files=comp_data.get("files", []),
                dependencies=comp_data.get("dependencies", []),
            )
        scripts = {k: str(v) for k, v in data.get("scripts", {}).items()}
        return cls(
            name=data.get("name", ""),
            components=components,
            scripts=scripts,
        )


def load_manifest(directory: Path) -> Optional[SpindleManifest]:
    """Load manifest from spindle.yaml, spindle.json, or spindle.toml."""
    # 1) spindle.yaml
    yaml_path = directory / "spindle.yaml"
    if yaml_path.exists():
        manifest = _load_manifest_yaml(yaml_path)
        if manifest:
            return manifest

    # 2) spindle.json
    json_path = directory / "spindle.json"
    if json_path.exists():
        manifest = _load_manifest_json(json_path)
        if manifest:
            return manifest

    # 3) spindle.toml
    toml_path = directory / "spindle.toml"
    if toml_path.exists():
        manifest = _load_manifest_toml(toml_path)
        if manifest:
            return manifest

    return None


def _load_manifest_yaml(path: Path) -> Optional[SpindleManifest]:
    """Load manifest from YAML file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return SpindleManifest.from_dict(data)
    except Exception:
        pass
    return None


def _load_manifest_json(path: Path) -> Optional[SpindleManifest]:
    """Load manifest from JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return SpindleManifest.from_dict(data)
    except Exception:
        pass
    return None


def _load_manifest_toml(path: Path) -> Optional[SpindleManifest]:
    """Load manifest from TOML file."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        if isinstance(data, dict):
            return SpindleManifest.from_dict(data)
    except Exception:
        pass
    return None


def install_component(identifier: str) -> bool:
    """Install a component from a Git repository.
    
    Returns True on success, False on failure.
    """
    comp_id = ComponentIdentifier.parse(identifier)
    if not comp_id:
        print(f"Error: Invalid component format. Expected 'GitHubUser/repo/path'.")
        return False

    with tempfile.TemporaryDirectory(prefix="spindle-") as temp_dir:
        temp_path = Path(temp_dir)

        # Fetch the repository
        if not _fetch_repository(comp_id, temp_path):
            return False

        # Read the manifest
        manifest = load_manifest(temp_path)
        if not manifest:
            print(f"Error: No spindle.yaml, spindle.json, or spindle.toml found in repository.")
            return False

        print(f"Successfully fetched and parsed manifest for '{manifest.name}'.")

        # Resolve dependencies
        files_to_install: Set[str] = set()
        visited: Set[str] = set()

        try:
            _resolve_dependencies(comp_id.path, manifest, files_to_install, visited)
        except Exception as e:
            print(f"Error: {e}")
            return False

        # Install files
        dest_root = Path.cwd() / "spindle"
        print(f"Installing component(s) into '{dest_root}'...")

        installed_dirs: Set[Path] = set()

        for file in sorted(files_to_install):
            source_path = temp_path / file
            dest_path = dest_root / file
            dest_dir = dest_path.parent

            # Ensure destination directory exists
            dest_dir.mkdir(parents=True, exist_ok=True)
            installed_dirs.add(dest_dir)

            # Copy file
            if dest_path.exists():
                dest_path.unlink()
            shutil.copy2(source_path, dest_path)
            print(f"  - Copied {file}")

        # Create __init__.py files for Python packages
        _create_init_py_files(installed_dirs, dest_root)

        print("Installation complete.")
        return True


def _fetch_repository(comp_id: ComponentIdentifier, dest: Path) -> bool:
    """Fetch repository using GitHub API or git clone."""
    token = os.environ.get("GITHUB_TOKEN")

    if token:
        print("GITHUB_TOKEN found. Attempting to download via API...")
        if _download_tarball(comp_id.user, comp_id.repo, token, dest):
            return True
        print("API download failed. Falling back to git clone.")

    print("Using git clone.")
    return _git_clone(comp_id.user, comp_id.repo, dest)


def _download_tarball(user: str, repo: str, token: str, dest: Path) -> bool:
    """Download and extract repository tarball from GitHub API."""
    try:
        url = f"https://api.github.com/repos/{user}/{repo}/tarball/main"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Save tarball
        tar_path = dest / "repo.tar.gz"
        with open(tar_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extract
        result = subprocess.run(
            ["tar", "-xzf", str(tar_path), "-C", str(dest), "--strip-components=1"],
            capture_output=True,
        )
        tar_path.unlink()

        return result.returncode == 0
    except Exception:
        return False


def _git_clone(user: str, repo: str, dest: Path) -> bool:
    """Clone repository using git."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/{user}/{repo}.git", "."],
            cwd=dest,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def _resolve_dependencies(
    component_name: str,
    manifest: SpindleManifest,
    files_to_install: Set[str],
    visited: Set[str],
) -> None:
    """Recursively resolve component dependencies."""
    if component_name in visited:
        return
    visited.add(component_name)

    # Handle wildcard for all components
    if component_name == "*":
        for name in manifest.components:
            _resolve_dependencies(name, manifest, files_to_install, visited)
        return

    if component_name not in manifest.components:
        raise ValueError(f"Component '{component_name}' not found in manifest.")

    component = manifest.components[component_name]

    # Resolve dependencies first
    for dep in component.dependencies:
        _resolve_dependencies(dep, manifest, files_to_install, visited)

    # Add this component's files
    files_to_install.update(component.files)


def _create_init_py_files(directories: Set[Path], root: Path) -> None:
    """Create __init__.py files in all directories up to root."""
    all_dirs = set(directories)
    all_dirs.add(root)

    # Collect all parent directories up to root
    parents_to_ensure: Set[Path] = set()
    for dir_path in all_dirs:
        current = dir_path
        while str(current).startswith(str(root)) and len(str(current)) >= len(str(root)):
            parents_to_ensure.add(current)
            if current == root:
                break
            current = current.parent

    # Create __init__.py in each directory
    for dir_path in parents_to_ensure:
        init_py = dir_path / "__init__.py"
        if not init_py.exists():
            init_py.touch()
            rel_path = dir_path.relative_to(root.parent)
            print(f"  - Created __init__.py in ./{rel_path}")
