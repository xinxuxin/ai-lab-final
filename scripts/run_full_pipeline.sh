#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
source .venv/bin/activate

cd backend
PYTHONPATH=src ../.venv/bin/python -m cli.main build-corpus --raw-dir ../data/raw --output-dir ../data/processed --input ../data/selected_products.jsonl
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product desk-lamp-with-usb-ports-includes-led-light-bulb-threshold-8482-80705997 --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product desk-lamp-with-usb-ports-includes-led-light-bulb-threshold-8482-80705997 --mode review_informed_rag
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product jbl-tour-one-m2-wireless-over-ear-adaptive-noise-cancelling-headphones-black-89301002 --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product jbl-tour-one-m2-wireless-over-ear-adaptive-noise-cancelling-headphones-black-89301002 --mode review_informed_rag
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product levoit-core-300-air-purifier-white-81910071 --mode baseline_description_only
PYTHONPATH=src ../.venv/bin/python -m cli.main extract-visual-profile --product levoit-core-300-air-purifier-white-81910071 --mode review_informed_rag
PYTHONPATH=src ../.venv/bin/python -m cli.main generate-images --all --count 4
PYTHONPATH=src ../.venv/bin/python -m cli.main evaluate-images --all
PYTHONPATH=src ../.venv/bin/python -m cli.main run-workflow --all
PYTHONPATH=src ../.venv/bin/python -m cli.main verify-artifacts --stage full --frontend-dir ../frontend
