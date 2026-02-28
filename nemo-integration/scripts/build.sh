#!/bin/bash
# Build script for the NeMo scaffold module.
# Installs baseline Python dependency for local smoke training.

set -e

echo "=== NeMo Scaffold Module: Build ==="

python3 -c "import numpy; print(f'numpy version: {numpy.__version__}')" 2>/dev/null || {
    echo "numpy not found; installing..."
    pip install numpy 2>/dev/null || pip install --user numpy
}

echo "=== Build complete ==="
