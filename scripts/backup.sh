#!/usr/bin/env bash
# Sao lưu toàn bộ dữ liệu (PostgreSQL) ra file .dump trong thư mục backups/.
#   ./scripts/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
FILE="backups/lichhoc-$(date +%Y%m%d-%H%M).dump"
docker compose exec -T db pg_dump -U lichhoc -Fc lichhoc >"$FILE"
echo "Đã sao lưu: $FILE ($(du -h "$FILE" | cut -f1))"
