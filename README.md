# Spindle

A command-line tool for installing and managing reusable source code components directly into your project, with npm-like script running capabilities.

## Overview

Spindle is inspired by the philosophy of `shadcn-ui`. Instead of adding dependencies to your project, it copies the source code of components directly into your local codebase, giving you full control to inspect, edit, and adapt them to your needs.

This approach is designed for developers who want to use well-crafted components without being locked into a library's specific implementation or dealing with dependency conflicts.

## Features

- **Local Source Installation**: Install components directly into a `spindle/` directory in your project
- **Granular Control**: Install entire packages or individual, specific modules
- **Automatic Dependency Resolution**: Automatically finds and installs all required dependencies
- **Multi-Language Support**: Initial support for Python and TypeScript projects
- **Fully Editable Code**: Since the code lives in your project, you can modify it as needed
- **Script Runner**: Run project commands with npm-like shortcuts (similar to `npm run`)

## Installation

### Homebrew (recommended)

```bash
brew tap spninad/tap
brew install spindle
```

Or in one line:

```bash
brew install spninad/tap/spindle
```

### pip

```bash
pip install spindle-cli
```

The wheel bundles a pre-compiled native binary — no Swift toolchain required.

### Build from source

Requires the Swift toolchain:

```bash
swift build -c release
# binary at .build/release/spindle
```

## Usage

### Installing Components

Install components from Git repositories using the `install` command:

```bash
# Install an entire package
spindle install GitHubUser/mango/*

# Install a specific module
spindle install GitHubUser/mango/torch/vision_transformer
```

The component identifier is a path that includes the Git source and the path to the component within the repository. When you install a module, Spindle automatically installs all of its dependencies as defined in the repository's `spindle.json` manifest.

#### Using Installed Components

**Python:**
```python
from spindle.mango.torch.vision_transformer import VisionTransformer
```

**TypeScript:**
```typescript
import { logger } from '@spindle/mango/utils/logger';
```

### Running Scripts

Spindle includes an npm-like script runner that lets you define and run project commands without custom shell scripts.

#### Configuration

Define scripts in one of four supported configuration files (checked in this order):

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

3. **`spindle.toml`**

```toml
[scripts]
start = "uvicorn app:app --reload"
dev = "python -m myapp"
build = "tsc -p tsconfig.json"
test = "pytest -q"
deploy = "fly deploy"
seed = "python scripts/seed.py"
```

4. **`pyproject.toml`**

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

**Shortcut commands** - These can be run directly without the `run` prefix:
- `spindle start`
- `spindle dev`
- `spindle launch`
- `spindle build`
- `spindle test`
- `spindle deploy`

**Generic command** - For any other script name:
- `spindle run <script-name>`

#### Passing Arguments

Arguments after the script name are passed through to the underlying command:

```bash
# Shortcut scripts with arguments
spindle start
spindle dev -- --port 8080
spindle test -- -k "fast and not slow"

# Generic scripts with arguments
spindle run seed
spindle run migrate -- --dry-run
spindle run deploy -- --env=production
```

Scripts run in the current working directory using `/bin/bash -lc "<command>"`, and exit codes are propagated to the terminal.

## Examples

### Complete Workflow

1. Create a configuration file:

```yaml
# spindle.yaml
scripts:
  dev: python -m uvicorn app:app --reload --port 8000
  test: pytest tests/ -v
  lint: ruff check .
  format: black .
  migrate: alembic upgrade head
```

2. Run your scripts:

```bash
# Start development server
spindle dev

# Run tests
spindle test

# Run with custom arguments
spindle dev -- --port 3000
spindle test -- tests/unit/ -k "user"
```

### Using with Python Projects

```yaml
# spindle.yaml
scripts:
  dev: python -m myapp
  test: pytest
  lint: ruff check src/
  type-check: mypy src/
  format: black src/
```

### Using with TypeScript Projects

```yaml
# spindle.yaml
scripts:
  dev: tsx watch src/index.ts
  build: tsc -p tsconfig.json
  test: vitest
  lint: eslint src/
  format: prettier --write src/
```

## Component Manifest Format

Repositories that provide components must include a manifest file at their root. Spindle supports three formats (checked in this order):

1. **`spindle.yaml`** (recommended)
2. **`spindle.json`**
3. **`spindle.toml`**

### YAML Example

```yaml
name: mango-components
components:
  torch/transformer:
    files:
      - python/mango/torch/transformer.py
    dependencies: []
  torch/vision_transformer:
    files:
      - python/mango/torch/vision_transformer.py
    dependencies:
      - torch/transformer
  utils/logger:
    files:
      - typescript/mango/utils/logger.ts
    dependencies: []
```

### JSON Example

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

### TOML Example

```toml
name = "mango-components"

[components."torch/transformer"]
files = ["python/mango/torch/transformer.py"]
dependencies = []

[components."torch/vision_transformer"]
files = ["python/mango/torch/vision_transformer.py"]
dependencies = ["torch/transformer"]

[components."utils/logger"]
files = ["typescript/mango/utils/logger.ts"]
dependencies = []
```

### Manifest Fields

- **`name`**: A descriptive name for the component collection
- **`components`**: An object where each key is a unique identifier for a component
- **`files`**: An array of source file paths relative to the repository root
- **`dependencies`**: An array of other component identifiers from the same repository
- **`scripts`**: (Optional) Scripts that can be run with `spindle run` (same file can define both components and scripts)

## Authentication

For private repositories, Spindle supports two methods:

1. **GitHub API** (Recommended for CI): Set the `GITHUB_TOKEN` environment variable
2. **Git Clone** (Fallback): Uses your local Git credentials

## License

See the repository for license information.
