#!/bin/bash
# Test script for nb_bundle command

set -e

echo "=== Testing nb_bundle command ==="

# Setup test directory
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
echo "Test directory: $TEST_DIR"

# Create test files
echo "Creating test files..."

# utils.py
cat > utils.py << 'EOF'
"""Utility functions"""

def add(a, b):
    """Add two numbers"""
    return a + b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b
EOF

# helpers/data.py
mkdir -p helpers
cat > helpers/data.py << 'EOF'
"""Data processing helpers"""

def process_data(data):
    """Process data"""
    return [x * 2 for x in data]

def filter_data(data, threshold):
    """Filter data by threshold"""
    return [x for x in data if x > threshold]
EOF

# main.py
cat > main.py << 'EOF'
"""Main script"""
import utils
from helpers.data import process_data

result = utils.add(10, 20)
print(f"Result: {result}")

data = [1, 2, 3]
processed = process_data(data)
print(f"Processed: {processed}")
EOF

# Create a sample notebook
python3 << 'PYEOF'
import json

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# Test Notebook\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import utils\n",
                "from helpers.data import process_data\n",
                "\n",
                "result = utils.add(5, 3)\n",
                "print(result)\n"
            ]
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

with open('test.ipynb', 'w') as f:
    json.dump(notebook, f, indent=2)
PYEOF

echo "✓ Test files created"

# Test 1: Bundle notebook with dependencies
echo ""
echo "Test 1: Bundle notebook with dependencies"
SPINDLE_BIN="/home/runner/work/spindle/spindle/.build/debug/spindle"
$SPINDLE_BIN nb_bundle test.ipynb bundled.ipynb utils.py helpers/data.py
if [ -f bundled.ipynb ]; then
    echo "✓ Test 1 passed: bundled.ipynb created"
else
    echo "✗ Test 1 failed: bundled.ipynb not created"
    exit 1
fi

# Test 2: Bundle Python script with dependencies
echo ""
echo "Test 2: Bundle Python script with dependencies"
$SPINDLE_BIN nb_bundle main.py bundled_script.ipynb utils.py helpers/data.py
if [ -f bundled_script.ipynb ]; then
    echo "✓ Test 2 passed: bundled_script.ipynb created"
else
    echo "✗ Test 2 failed: bundled_script.ipynb not created"
    exit 1
fi

# Test 3: Verify bundled notebook structure
echo ""
echo "Test 3: Verify bundled notebook structure"
python3 << 'PYEOF'
import json
import sys

with open('bundled.ipynb', 'r') as f:
    notebook = json.load(f)

# Check for required cells
has_bundled_header = False
has_utils_writefile = False
has_data_writefile = False
has_original_cells = False

for cell in notebook['cells']:
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        if 'Bundled Dependencies' in source:
            has_bundled_header = True
    elif cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if '%%writefile utils.py' in source:
            has_utils_writefile = True
        elif '%%writefile helpers/data.py' in source:
            has_data_writefile = True
        elif 'result = utils.add(5, 3)' in source:
            has_original_cells = True

if not all([has_bundled_header, has_utils_writefile, has_data_writefile, has_original_cells]):
    print("✗ Test 3 failed: Missing expected cells")
    print(f"  Bundled header: {has_bundled_header}")
    print(f"  Utils writefile: {has_utils_writefile}")
    print(f"  Data writefile: {has_data_writefile}")
    print(f"  Original cells: {has_original_cells}")
    sys.exit(1)

print("✓ Test 3 passed: Bundled notebook has correct structure")
PYEOF

# Test 4: Error handling - missing input file
echo ""
echo "Test 4: Error handling - missing input file"
if $SPINDLE_BIN nb_bundle nonexistent.ipynb output.ipynb utils.py 2>&1 | grep -q "does not exist"; then
    echo "✓ Test 4 passed: Correctly reports missing input file"
else
    echo "✗ Test 4 failed: Should report missing input file"
    exit 1
fi

# Test 5: Error handling - missing dependency file
echo ""
echo "Test 5: Error handling - missing dependency file"
if $SPINDLE_BIN nb_bundle test.ipynb output.ipynb nonexistent.py 2>&1 | grep -q "do not exist"; then
    echo "✓ Test 5 passed: Correctly reports missing dependency file"
else
    echo "✗ Test 5 failed: Should report missing dependency file"
    exit 1
fi

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo ""
echo "=== All tests passed! ==="
