#!/usr/bin/env bash
# Khôi phục dữ liệu từ file .dump (ghi đè dữ liệu hiện tại).
#   ./scripts/restore.sh "$HOME/Library/Application Support/LichHocAgent/backups/lichhoc-YYYYmmdd-HHMM.dump"
set -euo pipefail
FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
    echo "Dùng: $0 <file .dump>" >&2
    exit 2
fi
DB="$(docker ps -q --filter label=com.docker.compose.project=lichhoc --filter label=com.docker.compose.service=db)"
BACKEND="$(docker ps -q --filter label=com.docker.compose.project=lichhoc --filter label=com.docker.compose.service=backend)"
[[ -n "$DB" && -n "$BACKEND" ]] || { echo "Không thấy container lichhoc đang chạy." >&2; exit 1; }
read -r -p "Ghi đè dữ liệu hiện tại bằng $FILE? (y/N) " answer
[[ "$answer" == "y" || "$answer" == "Y" ]] || { echo "Đã huỷ."; exit 1; }
docker exec -i "$DB" pg_restore --clean --if-exists -U lichhoc -d lichhoc <"$FILE"
docker restart "$BACKEND" >/dev/null
echo "Đã khôi phục từ $FILE."
