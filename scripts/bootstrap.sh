#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
  echo "Fill in your Istari registry URL and PAT before running scripts."
fi

echo "Bootstrap complete."
echo "Run: source .venv/bin/activate && python istari_client.py"
