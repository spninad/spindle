# Spindle CLI (Python)

A command-line tool for installing and managing reusable source code components directly into your project, with npm-like script running capabilities.

## Installation

```bash
pip install spindle-cli
```

Or install from source:

```bash
cd python
pip install -e .
```

## Usage

### Installing Components

Install components from Git repositories:

```bash
# Install an entire package
spindle install GitHubUser/mango/*

# Install a specific module
spindle install GitHubUser/mango/torch/vision_transformer
```

### Running Scripts

Define scripts in `spindle.yaml`, `spindle.json`, or `pyproject.toml`:

```yaml
# spindle.yaml
scripts:
  start: uvicorn app:app --reload
  dev: python -m myapp
  test: pytest -q
```

Run scripts:

```bash
# Shortcut commands
spindle start
spindle dev
spindle test

# Generic command
spindle run <script-name>

# With arguments
spindle test -- -k "fast"
```

## Configuration

Scripts can be defined in (checked in this order):

1. `spindle.yaml`
2. `spindle.json`
3. `pyproject.toml` under `[tool.spindle.scripts]`

See the main README.md for full documentation.
