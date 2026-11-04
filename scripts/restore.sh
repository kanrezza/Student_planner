#!/usr/bin/env bash
# Khôi phục dữ liệu từ file .dump (ghi đè dữ liệu hiện tại).
#   ./scripts/restore.sh backups/lichhoc-YYYYmmdd-HHMM.dump
set -euo pipefail
cd "$(dirname "$0")/.."
FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
    echo "Dùng: $0 <file .dump>" >&2
    exit 2
fi
read -r -p "Ghi đè dữ liệu hiện tại bằng $FILE? (y/N) " answer
[[ "$answer" == "y" || "$answer" == "Y" ]] || { echo "Đã huỷ."; exit 1; }
docker compose exec -T db pg_restore --clean --if-exists -U lichhoc -d lichhoc <"$FILE"
docker compose restart backend >/dev/null
echo "Đã khôi phục từ $FILE."
