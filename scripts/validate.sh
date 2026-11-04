#!/usr/bin/env bash
# Chạy các kịch bản quickstart tự động được (V*, D*) trên database tạm, OCR thật (mất ~3 phút).
set -euo pipefail
cd "$(dirname "$0")/.."
DB=lichhoc_validate
docker compose up -d --wait db >/dev/null
docker compose exec -T db psql -U lichhoc -q -c "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB" >/dev/null
trap 'docker compose exec -T db psql -U lichhoc -q -c "DROP DATABASE IF EXISTS '$DB'" >/dev/null' EXIT
docker compose run --rm --quiet-pull -v "$PWD/backend:/app" \
    -e DATABASE_URL="postgresql+psycopg://lichhoc:lichhoc@db:5432/$DB" -e PYTHONPATH=/app \
    backend sh -c "flask db upgrade >/dev/null 2>&1 && python /app/scripts_validate.py"
