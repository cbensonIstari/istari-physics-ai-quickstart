#!/bin/bash
# Install script for the NeMo scaffold integration module.
# Copies files to the Istari agent module directory.

set -e

echo "=== NeMo Scaffold Module: Install ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# IMPORTANT: Do NOT nest under @istari/ namespace directories.
if [[ "$(uname)" == "Darwin" ]]; then
    DEFAULT_DIR="$HOME/Library/Application Support/istari_agent/istari_modules/nemo"
else
    DEFAULT_DIR="/opt/local/istari_agent/istari_modules/nemo"
fi
INSTALL_DIR="${ISTARI_MODULES_DIR:-$DEFAULT_DIR}"

echo "Installing to: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cp -r "$MODULE_DIR/src" "$INSTALL_DIR/"
cp -r "$MODULE_DIR/function_schemas" "$INSTALL_DIR/"
cp "$MODULE_DIR/module_manifest.json" "$INSTALL_DIR/"

echo "=== Install complete ==="
