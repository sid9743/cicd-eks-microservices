#!/usr/bin/env bash
# Runs unit tests for one service inside a throwaway virtualenv.
set -euo pipefail

SERVICE="${1:?usage: run-tests.sh <service-name>}"
cd "services/${SERVICE}"

python3 -m venv .venv
. .venv/bin/activate
pip install --quiet -r requirements-dev.txt
pytest --cov=app --cov-report=xml:coverage.xml --junitxml=test-results.xml
