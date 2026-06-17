#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(dirname "$SCRIPT_DIR")
cd "$REPO_ROOT"

if [ ! -f ".env" ]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example. Fill DEEPSEEK_API_KEY for live generation."
fi

if [ "${1:-}" = "--skip-build" ]; then
  docker compose up -d
else
  docker compose up --build -d
fi

echo ""
echo "PathFinder Lite is starting."
echo "App:    http://localhost:8000/app"
echo "Status: http://localhost:8000/api/status"
echo "Demos:"
echo "  http://localhost:8000/app/external-plan-audit-demo"
echo "  http://localhost:8000/app/admissions-opportunity-demo"
