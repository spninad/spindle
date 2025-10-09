# Notebook Bundling with `nb_bundle`

## Overview

The `nb_bundle` command is a utility for bundling Python dependencies into a single, self-contained Jupyter notebook. This is particularly useful when:

- You want to share a notebook that depends on multiple Python files
- You need to run notebooks in environments where you can't easily distribute multiple files
- You want to create reproducible, standalone notebooks for teaching or demonstrations
- You need to submit a single notebook file for assignments or competitions

## How It Works

When you run `nb_bundle`, it:

1. Reads your input notebook or Python script
2. Reads all the Python files you want to bundle
3. Creates a new notebook with:
   - Header cells explaining the bundled dependencies
   - `%%writefile` magic cells that recreate each Python file
   - Directory creation cells for any nested paths
   - All your original notebook cells (or the converted Python script)

When someone runs the bundled notebook, the initial cells execute and recreate all the dependent Python files, making them available for import in subsequent cells.

## Usage

### Basic Syntax

```bash
spindle nb_bundle <input> <output> <file1> [<file2> ...]
```

- `<input>`: Your input notebook (`.ipynb`) or Python script (`.py`)
- `<output>`: The output bundled notebook (`.ipynb`)
- `<file1> [<file2> ...]`: Python files to bundle

### Examples

#### Example 1: Bundle a notebook with utilities

Suppose you have:
- `analysis.ipynb` - your main notebook
- `utils.py` - utility functions
- `helpers/data.py` - data processing helpers

```bash
spindle nb_bundle analysis.ipynb bundled_analysis.ipynb utils.py helpers/data.py
```

The output `bundled_analysis.ipynb` will be self-contained and can be shared without the `.py` files.

#### Example 2: Convert a Python script to a notebook with dependencies

If you have a Python script that imports local modules:

```bash
spindle nb_bundle main.py notebook.ipynb module1.py module2.py
```

This converts `main.py` to a notebook and bundles the dependencies.

#### Example 3: Using a working directory

If your files are in a specific directory:

```bash
spindle nb_bundle notebook.ipynb output.ipynb utils.py --working-dir /path/to/project
```

## Structure of Bundled Notebooks

A bundled notebook has the following structure:

1. **Bundled Dependencies Header** - A markdown cell explaining the bundled files
2. **File Recreation Cells** - For each bundled file:
   - Directory creation cell (if needed)
   - Markdown header with the file path
   - `%%writefile` cell with the file contents
3. **Main Code Separator** - A markdown cell separating bundled files from your code
4. **Original Cells** - All your original notebook cells

### Example Output

```
# Bundled Dependencies

The following cells write the required Python files to disk.

---

## utils.py

%%writefile utils.py
def add(a, b):
    return a + b

---

import os
os.makedirs('helpers', exist_ok=True)

## helpers/data.py

%%writefile helpers/data.py
def process_data(data):
    return [x * 2 for x in data]

---

# Main Code

[Your original cells follow here]
```

## Best Practices

1. **Run cells in order**: The bundled notebook must be run from top to bottom at least once to create the Python files.

2. **Restart kernel when sharing**: Before sharing, restart the kernel and run all cells to ensure everything works from a clean state.

3. **Keep paths consistent**: Use the same import paths in your original notebook as the file paths you specify to `nb_bundle`.

4. **Test the bundled notebook**: Always test the bundled notebook in a clean environment to ensure all dependencies are properly included.

5. **Document dependencies**: Consider adding a markdown cell listing any pip-installable dependencies that still need to be installed.

## Limitations

- Only bundles Python files (`.py`). Other file types (data files, configs, etc.) are not supported.
- The bundled files must be valid Python files that can be written to disk and imported.
- External pip packages still need to be installed separately - only local Python files are bundled.

## Common Issues

### Import errors after bundling

If you get import errors in the bundled notebook:
- Make sure you specified all dependent files to `nb_bundle`
- Check that the file paths you specified match the import statements in your code
- Verify that all cells are executed in order

### File path issues

If files aren't being created in the right location:
- Make sure you're using relative paths, not absolute paths
- Use the `--working-dir` option if needed to set the correct base directory
- Check that nested directories are being created (look for the `os.makedirs` cells)

## Advanced Usage

### Bundling deeply nested modules

If you have a complex project structure:

```bash
spindle nb_bundle notebook.ipynb output.ipynb \
  src/utils/math.py \
  src/utils/string.py \
  src/data/loader.py \
  src/data/processor.py
```

All directory structures will be preserved in the bundled notebook.

### Combining with Spindle components

You can use `nb_bundle` with components installed via `spindle install`:

```bash
# First, install components
spindle install GitHubUser/mylib/component

# Then bundle them into a notebook
spindle nb_bundle notebook.ipynb bundled.ipynb spindle/mylib/component.py
```

This creates a truly standalone notebook that doesn't even require Spindle to run.
