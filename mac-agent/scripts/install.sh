#!/usr/bin/env bash
# Cài LichHocAgent (đồng bộ Lịch/Lời nhắc) chạy nền, tự khởi động khi đăng nhập.
#
#   mac-agent/scripts/install.sh               # build + cài + chạy
#   mac-agent/scripts/install.sh --build-only  # chỉ build mac-agent/dist/LichHocAgent.app (không cài)
#   mac-agent/scripts/install.sh --uninstall   # gỡ (giữ lại state và log)
#
# Ghi chú (research R4):
# - Cần Python dạng framework (Homebrew python@3.11); Python do uv cài không chạy được py2app.
# - py2app được chạy trong thư mục tạm không có pyproject.toml (tránh lỗi "install_requires").
# - Agent + môi trường Python riêng được cài hẳn vào ~/Library/Application Support/LichHocAgent, LaunchAgent
#   trỏ vào đó → tháo ổ SSD chứa thư mục dự án thì agent vẫn chạy. Sau khi cài không còn gì trỏ vào dự án.
# - App được ký ad-hoc; lần chạy đầu macOS sẽ hỏi quyền Lịch và Lời nhắc → bấm "Cho phép".
set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="/opt/homebrew/opt/python@3.11/bin/python3.11"
LABEL="vn.lichhoc.agent"
APP_NAME="LichHocAgent.app"
SUPPORT="$HOME/Library/Application Support/LichHocAgent"
VENV="$SUPPORT/venv"
APP_DEST="$SUPPORT/$APP_NAME"
LEGACY_APP="$HOME/Applications/$APP_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

stop_agent() {
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
}

uninstall() {
    stop_agent
    rm -f "$PLIST_DEST"
    rm -rf "$APP_DEST" "$LEGACY_APP" "$VENV"
    echo "Đã gỡ LichHocAgent."
    echo "State giữ lại tại: $SUPPORT (xoá tay nếu muốn)."
    echo "Lịch \"Lịch Học Cá Nhân\" vẫn còn: tắt đồng bộ trong ứng dụng TRƯỚC khi gỡ để xoá nó."
}

# build <thư mục đích>: tạo venv riêng ở $VENV rồi build LichHocAgent.app vào <thư mục đích>.
build() {
    local out="$1"
    if [[ ! -x "$PYTHON" ]]; then
        echo "Thiếu Python 3.11 của Homebrew. Cài bằng: brew install python@3.11" >&2
        exit 1
    fi
    mkdir -p "$SUPPORT"
    if [[ ! -x "$VENV/bin/python" ]]; then
        "$PYTHON" -m venv "$VENV"
    fi
    "$VENV/bin/pip" install --quiet --disable-pip-version-check \
        "pyobjc-framework-EventKit>=10.3" "pyobjc-framework-UserNotifications>=10.3" \
        "requests>=2.32" "py2app>=0.28.8"

    local work
    work="$(mktemp -d)"
    cp "$AGENT_DIR/setup.py" "$AGENT_DIR/app_plist.py" "$work/"
    cp -R "$AGENT_DIR/lichhoc_agent" "$work/"
    find "$work" -name '__pycache__' -prune -exec rm -rf {} +
    (cd "$work" && "$VENV/bin/python" setup.py py2app \
        --dist-dir "$work/dist" --bdist-base "$work/build" >"$work/py2app.log" 2>&1) || {
        echo "Build thất bại, xem log: $work/py2app.log" >&2
        exit 1
    }
    codesign --force --deep -s - "$work/dist/$APP_NAME"
    rm -rf "$out/$APP_NAME"
    mkdir -p "$out"
    ditto "$work/dist/$APP_NAME" "$out/$APP_NAME"
    rm -rf "$work"
    echo "Đã build: $out/$APP_NAME"
}

install() {
    stop_agent
    build "$SUPPORT"
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/LichHocAgent"
    rm -rf "$LEGACY_APP"
    sed -e "s#__APP__#$APP_DEST#g" -e "s#__HOME__#$HOME#g" \
        "$AGENT_DIR/launchd/$LABEL.plist" >"$PLIST_DEST"
    plutil -lint "$PLIST_DEST" >/dev/null
    if grep -q "/Volumes" "$PLIST_DEST"; then
        echo "LaunchAgent còn trỏ vào /Volumes: $PLIST_DEST" >&2
        exit 1
    fi
    launchctl bootstrap "$DOMAIN" "$PLIST_DEST"
    echo "Đã cài và chạy LichHocAgent tại: $SUPPORT"
    echo "Log: ~/Library/Logs/LichHocAgent/agent.log"
    echo "Nếu macOS hỏi quyền Lịch và Lời nhắc, hãy bấm \"Cho phép\"."
    echo "Sao lưu tự động: lần đầu ghi vào iCloud Drive / ổ rời, macOS có thể hỏi quyền truy cập thư mục"
    echo "và quyền gửi thông báo cho LichHocAgent — hãy bấm \"Cho phép\"."
}

case "${1:-}" in
    --uninstall) uninstall ;;
    --build-only) build "$AGENT_DIR/dist" ;;
    "") install ;;
    *) echo "Dùng: $0 [--build-only | --uninstall]" >&2; exit 2 ;;
esac
