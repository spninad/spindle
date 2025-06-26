# Spindle CLI: Project Specification

## 1. Overview

Spindle is a command-line interface (CLI) tool for installing and managing reusable source code components directly into your project. Inspired by the philosophy of `shadcn-ui`, Spindle is not a traditional package manager. Instead of adding a dependency to your project, it copies the source code of components (or "modules") into your local codebase, giving you full control to inspect, edit, and adapt them to your needs.

This approach is designed for developers who want to use well-crafted components without being locked into a library's specific implementation or dealing with dependency conflicts.

## 2. Core Features

- **Local Source Installation:** Install components directly into a `spindle/` directory in your project.
- **Granular Control:** Install entire packages (e.g., `mango/*`) or individual, specific modules (e.g., `mango/torch/vision_transformer`).
- **Automatic Dependency Resolution:** When you install a module, Spindle automatically finds and installs all of its required dependencies.
- **Multi-Language Support:** Initial support for Python and TypeScript projects.
- **Fully Editable Code:** Since the code lives in your project, you can modify it as you see fit. No black boxes.
- **Simple CLI:** A straightforward and easy-to-use command-line interface.

## 3. CLI Usage

The primary command is `install`. The CLI can be invoked via `spindle` or its shorter alias, `sp`. The component identifier is a path that includes the Git source and the path to the component within the repository.

### To install an entire package:

This command will install all modules from the `mango` repository owned by `GitHubUser`.

```bash
spindle install GitHubUser/mango/*
```

### To install a specific module:

This command will install the `vision_transformer` module from the `torch` directory within the `GitHubUser/mango` repository. It will also install any dependencies defined in the repository's `spindle.json`.

```bash
spindle install GitHubUser/mango/torch/vision_transformer
```

## 4. Architecture and Implementation

### 4.1. CLI Tool

The CLI will be a native application written in **Swift**, using Apple's `swift-argument-parser` library for robust command-line argument parsing. This ensures high performance and a small footprint.

### 4.2. Decentralized Package Sources

Spindle does not rely on a central package registry. Instead, it fetches components directly from Git repositories (e.g., GitHub). Each component repository is expected to contain a `spindle.json` manifest file at its root, which defines the available components and their dependencies.

This approach makes the system decentralized, as any repository can become a source of components simply by including a `spindle.json` file.

**Example `spindle.json` at the root of `GitHubUser/mango`:**

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

- **`name`**: A descriptive name for the component collection.
- **`components`**: An object where each key is a unique identifier for a component within the repository.
- **`files`**: An array of source file paths relative to the repository root.
- **`dependencies`**: An array of other component identifiers *from the same repository* that this component depends on.

### 4.3. Installation Process

1.  **Parse Command:** The CLI parses the `install` command and the component identifier (e.g., `GitHubUser/repo/path/to/module`).
2.  **Identify Source:** It identifies the source repository (e.g., `github.com/GitHubUser/repo`).
3.  **Fetch Repository:** Spindle uses a dual strategy to fetch the repository:
    - **GitHub API (Primary):** If a `GITHUB_TOKEN` environment variable is found, Spindle will use the GitHub API to download a `.zip` archive of the repository. This is fast and ideal for CI environments.
    - **`git clone` (Fallback):** If no token is found or the API fails, it falls back to performing a shallow clone (`git clone --depth 1`). This uses the user's local Git credentials, providing secure access to private repositories.
4.  **Prepare Source:** The downloaded archive is unzipped, or the cloned repository is used directly in a temporary local directory.
5.  **Read Manifest:** It reads the `spindle.json` manifest from the root of the source code.
6.  **Resolve Dependencies:** It looks up the requested component in the manifest and recursively resolves its dependency tree.
7.  **Install Files:** It copies the required source files from the temporary directory into the local `spindle/` directory.
8.  **Cleanup:** It deletes the temporary directory.

### 4.4. Language-Specific Handling

#### Python

- **Installation:** Files will be placed in `spindle/`, and `__init__.py` files will be created automatically in each subdirectory to make them importable Python packages.
- **Usage:** You can then import the modules using their path from the `spindle` root.

  ```python
  # After running `spindle install mango/torch/vision_transformer`
  from spindle.mango.torch.vision_transformer import VisionTransformer
  ```

- **Note on Root Imports:** The request for direct imports (e.g., `import vision_transformer`) is complex to achieve robustly without potentially interfering with the user's project setup (e.g., by modifying `sys.path` globally or creating symlinks in source roots). The proposed approach (`from spindle...`) is cleaner, more explicit, and avoids side effects, while still providing editable, local code.

#### TypeScript

- **Installation:** Files are copied to `spindle/`.
- **Usage:** Spindle will detect a `tsconfig.json` or `jsconfig.json` and offer to add a path alias.

  **Example `tsconfig.json` modification:**

  ```json
  {
    "compilerOptions": {
      "paths": {
        "@spindle/*": ["./spindle/*"]
      }
    }
  }
  ```

  This allows for clean imports in your TypeScript code:

  ```typescript
  import { logger } from '@spindle/mango/utils/logger';
  ```

## 5. Project Roadmap

- **Phase 1: Core CLI (MVP)**
  - [ ] Implement the `install` command in Swift.
  - [ ] Set up a sample package registry and repository.
  - [ ] Implement dependency resolution and file fetching.
  - [ ] Basic support for Python (file copy and `__init__.py` creation).
  - [ ] Basic support for TypeScript (file copy).

- **Phase 2: Enhancements**
  - [ ] Add `spindle init` command to configure the `spindle` directory and other settings in a `spindle.json` file.
  - [ ] Add `spindle list` to show all available packages from the registry.
  - [ ] Automatically update `tsconfig.json` for TypeScript projects.

- **Phase 3: Advanced Features**
  - [ ] Add `spindle update` to check for and apply updates to installed modules.
  - [ ] Diffing mechanism to show users what has changed in an update before they accept it.
  - [ ] Support for other languages (e.g., Go, Rust).
