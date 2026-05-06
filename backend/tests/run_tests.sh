#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "GaokaoAgent test runner"
echo "=========================================="

if [ ! -f "run_tests.py" ]; then
    echo "[ERROR] Run this script from backend/tests."
    exit 1
fi

python3 run_tests.py "$@"
