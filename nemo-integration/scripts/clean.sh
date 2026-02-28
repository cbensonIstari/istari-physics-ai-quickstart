#!/bin/bash
# Clean test temp files for NeMo scaffold module.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

rm -rf "$MODULE_DIR/test_files/train_nemo_surrogate/temp"
echo "Cleaned: $MODULE_DIR/test_files/train_nemo_surrogate/temp"
