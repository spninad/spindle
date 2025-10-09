# Spindle

A command-line interface (CLI) tool for installing and managing reusable source code components directly into your project.

## Overview

Spindle is not a traditional package manager. Instead of adding a dependency to your project, it copies the source code of components (or "modules") into your local codebase, giving you full control to inspect, edit, and adapt them to your needs.

Inspired by the philosophy of `shadcn-ui`, this approach is designed for developers who want to use well-crafted components without being locked into a library's specific implementation or dealing with dependency conflicts.

## Features

- **Local Source Installation:** Install components directly into a `spindle/` directory in your project
- **Granular Control:** Install entire packages or individual modules
- **Automatic Dependency Resolution:** Automatically find and install all required dependencies
- **Multi-Language Support:** Initial support for Python and TypeScript projects
- **Fully Editable Code:** Modify installed code as you see fit
- **Script Runner (npm-like):** Run project commands defined in `spindle.yaml`, `spindle.json`, or `pyproject.toml`
- **Notebook Bundling:** Bundle Python dependencies into self-contained Jupyter notebooks

## Installation

Build from source using Swift:

```bash
swift build -c release
```

The binary will be available at `.build/release/spindle`.

## Quick Start

### Install Components

```bash
# Install a specific module
spindle install GitHubUser/mango/torch/vision_transformer

# Install an entire package
spindle install GitHubUser/mango/*
```

### Run Scripts

Create a `spindle.yaml`, `spindle.json`, or add to your `pyproject.toml`:

```yaml
# spindle.yaml
scripts:
  start: uvicorn app:app --reload
  test: pytest -v
  deploy: fly deploy
```

Then run:

```bash
spindle start
spindle test
spindle run deploy
```

### Bundle Notebooks

Bundle Python dependencies into a single, self-contained Jupyter notebook:

```bash
spindle nb_bundle analysis.ipynb bundled.ipynb utils.py helpers/data.py
```

The bundled notebook can be shared and run independently, as it will recreate all the necessary Python files when executed.

## Documentation

- [Full Specification](SPEC.md) - Complete technical specification
- [Notebook Bundling Guide](docs/nb_bundle.md) - Detailed guide for the `nb_bundle` command

## Commands

- `spindle install <component>` - Install a component from a Git repository
- `spindle run <script>` - Run a configured script
- `spindle start`, `dev`, `launch`, `build`, `test`, `deploy` - Shortcut commands for common scripts
- `spindle nb_bundle <input> <output> <files...>` - Bundle Python files into a Jupyter notebook

## Requirements

- Swift 6.1 or later
- Git
- Python 3 (for nb_bundle command)

## License

See LICENSE file for details.
