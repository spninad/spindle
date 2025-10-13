# Spindle

A command-line tool for installing and managing reusable source code components directly into your project, with npm-like script running capabilities and support for bundling Python notebooks.

## Overview

Spindle is inspired by the philosophy of `shadcn-ui`. Instead of adding dependencies to your project, it copies the source code of components (or "modules") into your local codebase, giving you full control to inspect, edit, and adapt them to your needs.

This approach is designed for developers who want well-crafted components without being locked into a library's specific implementation or dealing with dependency conflicts.

Spindle is *not* a traditional package manager — it installs local source into a `spindle/` directory in your project so you can modify code directly.

## Features

* **Local Source Installation** — Install components directly into a `spindle/` directory in your project.
* **Granular Control** — Install entire packages or individual modules.
* **Automatic Dependency Resolution** — Automatically finds and installs all required dependencies declared by a component.
* **Multi-Language Support** — Initial support for Python and TypeScript projects.
* **Fully Editable Code** — Since the code lives in your project, you can modify it as needed.
* **Script Runner** — Run project commands with npm-like shortcuts (similar to `npm run`).
* **Notebook Bundling** — Bundle Python dependencies into self-contained Jupyter notebooks via the `nb_bundle` command.

## Installation

Build from source using Swift Package Manager:

```bash
swift build -c release
```

The executable will be available at:

```
.build/release/spindle
```

### Requirements

* Swift 6.1 or later
* Git
* Python 3 (required for `nb_bundle` and some Python-centric features)

## Quick Start

### Install Components

Install components from Git repositories using the `install` command. Component identifiers include the Git source and the path to the component within the repository.

```bash
# Install an entire package
spindle install GitHubUser/mango/*

# Install a specific module
spindle install GitHubUser/mango/torch/vision_transformer
```

When you install a module, Spindle automatically installs all of its dependencies as defined in the repository's `spindle.json` manifest.

#### Using Installed Components

**Python:**

```python
from spindle.mango.torch.vision_transformer import VisionTransformer
```

**TypeScript:**

```typescript
import { logger } from '@spindle/mango/utils/logger';
```

### Run Scripts

Spindle includes an npm-like script runner that lets you define and run project commands without custom shell scripts.

#### Configuration

Define scripts in one of three supported configuration files (checked in this order):

1. **`spindle.yaml`**

```yaml
scripts:
  start: uvicorn app:app --reload
  dev: python -m myapp
  build: tsc -p tsconfig.json
  test: pytest -q
  deploy: fly deploy
  seed: python scripts/seed.py
```

2. **`spindle.json`**

```json
{
  "scripts": {
    "start": "uvicorn app:app --reload",
    "dev": "python -m myapp",
    "build": "tsc -p tsconfig.json",
    "test": "pytest -q",
    "deploy": "fly deploy",
    "seed": "python scripts/seed.py"
  }
}
```

3. **`pyproject.toml`**

```toml
[tool.spindle.scripts]
start = "uvicorn app:app --reload"
dev = "python -m myapp"
build = "tsc -p tsconfig.json"
test = "pytest -q"
deploy = "fly deploy"
seed = "python scripts/seed.py"
```

The first file found is used.

#### Running Scripts

There are two ways to run scripts:

**Shortcut commands** — run directly without `run`:

* `spindle start`
* `spindle dev`
* `spindle launch`
* `spindle build`
* `spindle test`
* `spindle deploy`

**Generic command** — for any other script name:

* `spindle run <script-name>`

#### Passing Arguments

Arguments after the script name are passed through to the underlying command. Example:

```bash
# Shortcut scripts with arguments
spindle dev -- --port 8080
spindle test -- -k "fast and not slow"

# Generic scripts with arguments
spindle run migrate -- --dry-run
spindle run deploy -- --env=production
```

Scripts run in the current working directory using `/bin/bash -lc "<command>"`, and exit codes are propagated to the terminal.

### Notebook Bundling

Bundle Python dependencies and local files into a single, self-contained Jupyter notebook:

```bash
spindle nb_bundle analysis.ipynb bundled.ipynb utils.py helpers/data.py
```

The bundled notebook is built so it can recreate the necessary Python files when executed, making it portable and shareable.

## Commands

* `spindle install <component>` — Install a component from a Git repository (module or package).
* `spindle run <script>` — Run a configured script.
* Shortcut scripts: `spindle start`, `spindle dev`, `spindle launch`, `spindle build`, `spindle test`, `spindle deploy`.
* `spindle nb_bundle <input> <output> <files...>` — Bundle Python files into a Jupyter notebook.

## Usage Examples

### Complete Workflow (Python project)

1. Create `spindle.yaml`:

```yaml
scripts:
  dev: python -m uvicorn app:app --reload --port 8000
  test: pytest tests/ -v
  lint: ruff check .
  format: black .
  migrate: alembic upgrade head
```

2. Run:

```bash
spindle dev
spindle test
spindle dev -- --port 3000
```

### TypeScript project

```yaml
scripts:
  dev: tsx watch src/index.ts
  build: tsc -p tsconfig.json
  test: vitest
  lint: eslint src/
  format: prettier --write src/
```

## Component Manifest Format

Repositories that provide components must include a `spindle.json` manifest at their root:

```json
{
  "name": "mango-components",
  "components": {
    "torch/transformer": {
      "files": ["python/mango/torch/transformer.py"],
      "dependencies": []
    },
    "torch/vision_transformer": {
      "files": ["python/mango/torch/vision_transformer.py"],
      "dependencies": ["torch/transformer"]
    },
    "utils/logger": {
      "files": ["typescript/mango/utils/logger.ts"],
      "dependencies": []
    }
  }
}
```

Fields:

* **`name`** — A descriptive name for the component collection.
* **`components`** — An object where each key is a unique identifier for a component.
* **`files`** — An array of source file paths relative to the repository root.
* **`dependencies`** — An array of other component identifiers from the same repository.

## Authentication

For private repositories, Spindle supports two methods:

1. **GitHub API** (recommended for CI): set the `GITHUB_TOKEN` environment variable.
2. **Git Clone** (fallback): uses your local Git credentials.

## Documentation

* [Full Specification](SPEC.md) — Complete technical specification.
* [Notebook Bundling Guide](docs/nb_bundle.md) — Detailed guide for the `nb_bundle` command.

## License

See the repository LICENSE file for details.
