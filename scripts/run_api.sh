#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
exec uvicorn neural_architect.api.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
