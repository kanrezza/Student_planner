#!/usr/bin/env bash
# Cài LichHocAgent (đồng bộ Lịch/Lời nhắc) chạy nền, tự khởi động khi đăng nhập.
#
#   mac-agent/scripts/install.sh               # build + cài + chạy
#   mac-agent/scripts/install.sh --build-only  # chỉ build mac-agent/dist/LichHocAgent.app
#   mac-agent/scripts/install.sh --uninstall   # gỡ (giữ lại state và log)
#
# Ghi chú (research R4):
# - Cần Python dạng framework (Homebrew python@3.11); Python do uv cài không chạy được py2app.
# - py2app được chạy trong thư mục tạm không có pyproject.toml (tránh lỗi "install_requires").
# - App được ký ad-hoc; lần chạy đầu macOS sẽ hỏi quyền Lịch và Lời nhắc → bấm "Cho phép".
set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/opt/homebrew/opt/python@3.11/bin/python3.11"
LABEL="vn.lichhoc.agent"
APP_NAME="LichHocAgent.app"
APP_DEST="$HOME/Applications/$APP_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

stop_agent() {
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
}

uninstall() {
    stop_agent
    rm -f "$PLIST_DEST"
    rm -rf "$APP_DEST"
    echo "Đã gỡ LichHocAgent."
    echo "State giữ lại tại: ~/Library/Application Support/LichHocAgent (xoá tay nếu muốn)."
    echo "Lịch \"Lịch Học Cá Nhân\" vẫn còn: tắt đồng bộ trong ứng dụng TRƯỚC khi gỡ để xoá nó."
}

build() {
    if [[ ! -x "$PYTHON" ]]; then
        echo "Thiếu Python 3.11 của Homebrew. Cài bằng: brew install python@3.11" >&2
        exit 1
    fi
    if [[ ! -x "$AGENT_DIR/.venv/bin/python" ]]; then
        "$PYTHON" -m venv "$AGENT_DIR/.venv"
    fi
    "$AGENT_DIR/.venv/bin/pip" install --quiet --disable-pip-version-check \
        "pyobjc-framework-EventKit>=10.3" "requests>=2.32" "py2app>=0.28.8"

    local work
    work="$(mktemp -d)"
    cp "$AGENT_DIR/setup.py" "$AGENT_DIR/app_plist.py" "$work/"
    cp -R "$AGENT_DIR/lichhoc_agent" "$work/"
    find "$work" -name '__pycache__' -prune -exec rm -rf {} +
    (cd "$work" && "$AGENT_DIR/.venv/bin/python" setup.py py2app \
        --dist-dir "$work/dist" --bdist-base "$work/build" >"$work/py2app.log" 2>&1) || {
        echo "Build thất bại, xem log: $work/py2app.log" >&2
        exit 1
    }
    codesign --force --deep -s - "$work/dist/$APP_NAME"
    rm -rf "$AGENT_DIR/dist/$APP_NAME"
    mkdir -p "$AGENT_DIR/dist"
    ditto "$work/dist/$APP_NAME" "$AGENT_DIR/dist/$APP_NAME"
    rm -rf "$work"
    echo "Đã build: $AGENT_DIR/dist/$APP_NAME"
}

install() {
    build
    stop_agent
    mkdir -p "$HOME/Applications" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/LichHocAgent"
    rm -rf "$APP_DEST"
    ditto "$AGENT_DIR/dist/$APP_NAME" "$APP_DEST"
    sed "s#__HOME__#$HOME#g" "$AGENT_DIR/launchd/$LABEL.plist" >"$PLIST_DEST"
    plutil -lint "$PLIST_DEST" >/dev/null
    launchctl bootstrap "$DOMAIN" "$PLIST_DEST"
    echo "Đã cài và chạy LichHocAgent. Log: ~/Library/Logs/LichHocAgent/agent.log"
    echo "Nếu macOS hỏi quyền Lịch và Lời nhắc, hãy bấm \"Cho phép\"."
}

case "${1:-}" in
    --uninstall) uninstall ;;
    --build-only) build ;;
    "") install ;;
    *) echo "Dùng: $0 [--build-only | --uninstall]" >&2; exit 2 ;;
esac
