#!/usr/bin/env bash
# Chạy các kịch bản quickstart tự động được (V*, D*) trên database tạm, OCR thật (mất ~3 phút).
set -euo pipefail
cd "$(dirname "$0")/.."

# ./scripts/validate.sh search-perf  — quickstart S5: 1.000 task + một học kỳ đầy đủ, mỗi truy vấn < 0,3 giây.
# (Chạy trên database test riêng, không đụng dữ liệu thật.)
if [[ "${1:-}" == "search-perf" ]]; then
    docker compose up -d --wait db >/dev/null
    exec docker compose run --rm --quiet-pull -v "$PWD/backend:/app" backend \
        pytest tests/integration/test_search_perf.py -q -m slow
fi

# ./scripts/validate.sh backup-stale  — quickstart B5: giả lập "đã 4 ngày chưa sao lưu được".
# Dừng agent, lùi mốc sao lưu thành công gần nhất 4 ngày trong state.json, xoá dấu "đã báo", chạy lại.
# Hãy tháo ổ sao lưu (hoặc chọn thư mục không tồn tại) TRƯỚC, nếu không agent sẽ sao lưu bù ngay.
if [[ "${1:-}" == "backup-stale" ]]; then
    LABEL="vn.lichhoc.agent"
    DOMAIN="gui/$(id -u)"
    STATE="$HOME/Library/Application Support/LichHocAgent/state.json"
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    python3 - "$STATE" <<'PY'
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

path = Path(sys.argv[1])
state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
state["backup_last_success_at"] = (datetime.now() - timedelta(days=4)).isoformat()
state["backup_last_success_size"] = state.get("backup_last_success_size") or 1000
state["stale_notified_for"] = None
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
print("Đã lùi mốc sao lưu thành công gần nhất 4 ngày.")
PY
    launchctl bootstrap "$DOMAIN" "$HOME/Library/LaunchAgents/$LABEL.plist"
    echo "Đã chạy lại agent: thông báo macOS sẽ hiện trong vòng 1 phút."
    exit 0
fi
DB=lichhoc_validate
docker compose up -d --wait db >/dev/null
docker compose exec -T db psql -U lichhoc -q -c "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB" >/dev/null
trap 'docker compose exec -T db psql -U lichhoc -q -c "DROP DATABASE IF EXISTS '$DB'" >/dev/null' EXIT
docker compose run --rm --quiet-pull -v "$PWD/backend:/app" \
    -e DATABASE_URL="postgresql+psycopg://lichhoc:lichhoc@db:5432/$DB" -e PYTHONPATH=/app \
    backend sh -c "flask db upgrade >/dev/null 2>&1 && python /app/scripts_validate.py"
