#!/usr/bin/env bash
# Istari entrypoint wrapper for @istari:train_nemo_surrogate.
#
# This scaffold intentionally runs directly on the host Python runtime so that
# first-time integration tests can work on macOS/CPU.

set -euo pipefail

INPUT_FILE="$1"
OUTPUT_FILE="$2"
TEMP_DIR="$3"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$TEMP_DIR"

echo "[run_docker] launching local scaffold trainer"
echo "[run_docker] input_file:  $INPUT_FILE"
echo "[run_docker] output_file: $OUTPUT_FILE"
echo "[run_docker] temp_dir:    $TEMP_DIR"

python3 "$MODULE_ROOT/src/train_nemo_surrogate.py" "$INPUT_FILE" "$OUTPUT_FILE" "$TEMP_DIR"

echo "[run_docker] done"
