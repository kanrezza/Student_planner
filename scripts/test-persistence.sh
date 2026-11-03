#!/usr/bin/env bash
# Test tự động: dữ liệu còn nguyên sau khi khởi động lại và sau khi tắt đột ngột
# (constitution Nguyên tắc V, FR-024, SC-008). Chạy trên database chính; dữ liệu test có tiền tố
# "__persist_test__" và được dọn ở cuối (kể cả khi lỗi).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
check() { python3 "$ROOT/scripts/persistence_check.py" "$@"; }  # hàm: đường dẫn có dấu cách
SNAPSHOT="$(mktemp -t lichhoc-persist.XXXXXX)"

cleanup() {
    check cleanup >/dev/null 2>&1 || echo "⚠️  Chưa dọn được dữ liệu test (tiền tố __persist_test__)"
    rm -f "$SNAPSHOT"
}
trap cleanup EXIT

start_app() {
    docker compose up -d --wait >/dev/null 2>&1
}

echo "1. Bật ứng dụng và tạo dữ liệu thử"
start_app
check cleanup  # dọn dữ liệu sót từ lần chạy lỗi trước (nếu có)
check setup "$SNAPSHOT"

echo "2. Tắt ứng dụng (docker compose down, giữ volume) rồi bật lại"
docker compose down >/dev/null 2>&1
start_app
check verify "$SNAPSHOT"

echo "3. Ghi thêm một task rồi tắt đột ngột (kill backend + database)"
check add-task "$SNAPSHOT"
docker compose kill backend db >/dev/null 2>&1
start_app
check verify "$SNAPSHOT"

echo "✅ Dữ liệu còn nguyên sau khởi động lại và sau khi tắt đột ngột"
