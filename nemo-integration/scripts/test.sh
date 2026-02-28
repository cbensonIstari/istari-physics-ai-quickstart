#!/bin/bash
# Test script for the NeMo scaffold module.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
TEMP_DIR="$MODULE_DIR/test_files/train_nemo_surrogate/temp"
INPUT_FILE="$MODULE_DIR/test_files/train_nemo_surrogate/input.json"
OUTPUT_FILE="$TEMP_DIR/output_manifest.json"

echo "=== NeMo Scaffold Module: Test ==="
echo "Module dir: $MODULE_DIR"

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

cd "$MODULE_DIR"
bash src/run_docker.sh "$INPUT_FILE" "$OUTPUT_FILE" "$TEMP_DIR"

echo ""
echo "=== Verifying outputs ==="

PASS=0
FAIL=0

for expected in metrics.json model_checkpoint.npz training_report.md; do
    if [ -f "$TEMP_DIR/$expected" ]; then
        SIZE=$(wc -c < "$TEMP_DIR/$expected" | tr -d ' ')
        echo "  PASS  $expected ($SIZE bytes)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $expected (missing)"
        FAIL=$((FAIL + 1))
    fi
done

if [ -f "$OUTPUT_FILE" ]; then
    echo "  PASS  output_manifest.json"
    PASS=$((PASS + 1))
else
    echo "  FAIL  output_manifest.json (missing)"
    FAIL=$((FAIL + 1))
fi

if [ -f "$TEMP_DIR/metrics.json" ]; then
    HAS_VAL=$(python3 -c "import json; d=json.load(open('$TEMP_DIR/metrics.json')); print('yes' if 'val_metrics' in d else 'no')")
    if [ "$HAS_VAL" = "yes" ]; then
        echo "  PASS  metrics.json has val_metrics"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  metrics.json missing val_metrics"
        FAIL=$((FAIL + 1))
    fi
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
