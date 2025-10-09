#!/usr/bin/env python3
"""
Spindle nb_bundle - Bundle Python dependencies into a Jupyter notebook
"""
import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Set
import re


def create_writefile_cell(file_path: str, content: str) -> Dict[str, Any]:
    """Create a Jupyter notebook cell with %%writefile magic"""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            f"%%writefile {file_path}\n",
            content
        ]
    }


def create_markdown_cell(text: str) -> Dict[str, Any]:
    """Create a Jupyter notebook markdown cell"""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [text]
    }


def read_notebook(notebook_path: str) -> Dict[str, Any]:
    """Read a Jupyter notebook file"""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_python_file(file_path: str) -> str:
    """Read a Python file and return its contents"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_notebook_from_script(script_path: str) -> Dict[str, Any]:
    """Convert a Python script to a basic notebook structure"""
    content = read_python_file(script_path)
    
    # Create a basic notebook structure
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [content]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.x"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    return notebook


def bundle_notebook(input_path: str, output_path: str, files_to_bundle: List[str], 
                    working_dir: str = None) -> None:
    """
    Bundle Python files into a Jupyter notebook
    
    Args:
        input_path: Path to input notebook or Python script
        output_path: Path to output bundled notebook
        files_to_bundle: List of Python files to bundle
        working_dir: Working directory for resolving relative paths
    """
    if working_dir:
        os.chdir(working_dir)
    
    # Determine if input is a notebook or script
    is_notebook = input_path.endswith('.ipynb')
    
    if is_notebook:
        notebook = read_notebook(input_path)
    else:
        # Convert Python script to notebook
        notebook = create_notebook_from_script(input_path)
    
    # Validate files to bundle exist
    missing_files = []
    for file_path in files_to_bundle:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Error: The following files do not exist:", file=sys.stderr)
        for f in missing_files:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)
    
    # Prepare bundled cells
    bundled_cells = []
    
    # Add header
    bundled_cells.append(create_markdown_cell([
        "# Bundled Dependencies\n",
        "\n",
        "The following cells write the required Python files to disk.\n"
    ]))
    
    # Process each file to bundle
    processed_dirs: Set[str] = set()
    
    for file_path in files_to_bundle:
        # Read file content
        content = read_python_file(file_path)
        
        # Determine the directory path
        dir_path = os.path.dirname(file_path)
        
        # Create directory if needed (and not already processed)
        if dir_path and dir_path not in processed_dirs:
            # Add cell to create directory
            bundled_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f"import os\n",
                    f"os.makedirs('{dir_path}', exist_ok=True)\n"
                ]
            })
            processed_dirs.add(dir_path)
        
        # Add markdown header for this file
        bundled_cells.append(create_markdown_cell([
            f"## {file_path}\n"
        ]))
        
        # Add writefile cell
        bundled_cells.append(create_writefile_cell(file_path, content))
    
    # Add separator
    bundled_cells.append(create_markdown_cell([
        "---\n",
        "# Main Code\n"
    ]))
    
    # Insert bundled cells at the beginning
    notebook['cells'] = bundled_cells + notebook['cells']
    
    # Write output notebook
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2)
    
    print(f"Successfully bundled {len(files_to_bundle)} file(s) into {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Bundle Python dependencies into a Jupyter notebook',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bundle specific files into a notebook
  spindle nb_bundle main.ipynb output.ipynb utils.py helpers/data.py
  
  # Bundle a Python script with dependencies
  spindle nb_bundle main.py output.ipynb module1.py module2.py
        """
    )
    
    parser.add_argument('input', help='Input Jupyter notebook (.ipynb) or Python script (.py)')
    parser.add_argument('output', help='Output bundled Jupyter notebook (.ipynb)')
    parser.add_argument('files', nargs='+', help='Python files to bundle (can include nested paths)')
    parser.add_argument('--working-dir', '-w', help='Working directory for resolving relative paths')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Validate input file extension
    input_ext = os.path.splitext(args.input)[1]
    if input_ext not in ['.ipynb', '.py']:
        print(f"Error: Input file must be a .ipynb or .py file, got '{input_ext}'", file=sys.stderr)
        sys.exit(1)
    
    # Validate output file extension
    output_ext = os.path.splitext(args.output)[1]
    if output_ext != '.ipynb':
        print(f"Error: Output file must be a .ipynb file, got '{output_ext}'", file=sys.stderr)
        sys.exit(1)
    
    try:
        bundle_notebook(args.input, args.output, args.files, args.working_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
