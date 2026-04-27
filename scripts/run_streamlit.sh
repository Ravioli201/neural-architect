#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
exec streamlit run src/neural_architect/ui/streamlit_app.py "$@"
