#!/usr/bin/env bash
set -euo pipefail

echo "Checking QueryMind local stack files..."
test -f docker-compose.yml
test -f frontend/nginx.conf
test -f backend/sql/ddl/01_schema.sql
test -f backend/sql/warehouse/01_star_schema.sql
test -f backend/sql/seeds/seed_data.py

PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

echo "Checking Python syntax..."
"$PYTHON_BIN" backend/manage.py check

echo "Checking Angular TypeScript..."
(cd frontend && ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit)
echo "For full bundle verification, run separately: cd frontend && npm run build -- --progress=false"

echo "Local validation passed. Run: docker compose up --build"
