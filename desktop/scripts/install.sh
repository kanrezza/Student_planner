#!/usr/bin/env bash
# Build và cài app macOS "Lịch Học Cá Nhân.app" (Tauri 2).
#
#   desktop/scripts/install.sh               # build + ký + chép vào /Applications
#   desktop/scripts/install.sh --build-only  # chỉ build, không chép
#   desktop/scripts/install.sh --uninstall   # gỡ app khỏi /Applications (và ~/Applications nếu còn)
#
# Ghi chú: app được ký ad-hoc (không có Apple Developer ID) nên chỉ chạy trên máy build.
set -euo pipefail

DESKTOP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="Lịch Học Cá Nhân.app"
APP_BUILT="$DESKTOP_DIR/src-tauri/target/release/bundle/macos/$APP_NAME"
APP_DEST="/Applications/$APP_NAME"
OLD_DEST="$HOME/Applications/$APP_NAME" # nơi cài của các bản trước; được dọn khi cài/gỡ

# rustup cài cargo vào ~/.cargo/bin; shell chưa nạp thì tự thêm vào PATH.
[[ -d "$HOME/.cargo/bin" ]] && export PATH="$HOME/.cargo/bin:$PATH"

uninstall() {
    osascript -e 'tell application "Lịch Học Cá Nhân" to quit' >/dev/null 2>&1 || true
    rm -rf "$APP_DEST" "$OLD_DEST"
    echo "Đã gỡ $APP_NAME khỏi /Applications (và ~/Applications nếu còn)."
    echo "Dữ liệu công việc không bị ảnh hưởng (nằm trong OrbStack)."
}

build() {
    if ! command -v cargo >/dev/null 2>&1; then
        echo "Chưa cài Rust (cần để build app). Cài bằng lệnh sau rồi chạy lại script này:" >&2
        echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh" >&2
        exit 1
    fi
    cd "$DESKTOP_DIR"
    npm ci --no-audit --no-fund
    npx tauri build --bundles app
    codesign --force --deep -s - "$APP_BUILT"
    echo "Đã build: $APP_BUILT"
}

install() {
    build
    osascript -e 'tell application "Lịch Học Cá Nhân" to quit' >/dev/null 2>&1 || true
    rm -rf "$APP_DEST"
    ditto "$APP_BUILT" "$APP_DEST"
    if [[ -e "$OLD_DEST" ]]; then
        rm -rf "$OLD_DEST"
        echo "Đã xoá bản cũ ở ~/Applications."
    fi
    echo "Đã cài: $APP_DEST"
    echo "Mở app: open \"$APP_DEST\" (hoặc tìm \"Lịch Học Cá Nhân\" bằng Spotlight)."
}

case "${1:-}" in
    --uninstall) uninstall ;;
    --build-only) build ;;
    "") install ;;
    *) echo "Dùng: $0 [--build-only | --uninstall]" >&2; exit 2 ;;
esac
