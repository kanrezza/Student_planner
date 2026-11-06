#!/usr/bin/env bash
# Sao lưu toàn bộ dữ liệu (PostgreSQL) ra file .dump — mặc định nằm NGOÀI thư mục dự án:
#   ~/Library/Application Support/LichHocAgent/backups   (đổi bằng biến LICHHOC_BACKUP_DIR)
#   ./scripts/backup.sh
set -euo pipefail
DIR="${LICHHOC_BACKUP_DIR:-$HOME/Library/Application Support/LichHocAgent/backups}"
DB="$(docker ps -q --filter label=com.docker.compose.project=lichhoc --filter label=com.docker.compose.service=db)"
if [[ -z "$DB" ]]; then
    echo "Không thấy container db của lichhoc đang chạy." >&2
    exit 1
fi
mkdir -p "$DIR"
FILE="$DIR/lichhoc-$(date +%Y%m%d-%H%M).dump"
docker exec -i "$DB" pg_dump -U lichhoc -Fc lichhoc >"$FILE"
echo "Đã sao lưu: $FILE ($(du -h "$FILE" | cut -f1))"
