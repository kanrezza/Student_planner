#!/usr/bin/env bash
# Chạy TOÀN BỘ lint + test bằng một lệnh (constitution Nguyên tắc II).
#   ./scripts/test.sh          # backend, frontend, mac-agent, test lưu trữ
#   ./scripts/test.sh --ocr    # thêm bộ test OCR với ảnh mẫu (chậm)
# Trả mã thoát khác 0 nếu bất kỳ bước nào lỗi; cuối cùng in bảng tóm tắt.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RUN_OCR=false
[[ "${1:-}" == "--ocr" ]] && RUN_OCR=true

AGENT_PYTHON="/opt/homebrew/opt/python@3.11/bin/python3.11"  # mac-agent dùng Python 3.11 (research R4)
NPM_CACHE_ARGS=()
[[ -n "${NPM_CACHE:-}" ]] && NPM_CACHE_ARGS=(--cache "$NPM_CACHE")

declare -a RESULTS=()
FAILED=0

step() {
    local name="$1"
    shift
    echo
    echo "━━━ $name ━━━"
    local code=0
    "$@" || code=$?
    if [[ $code -eq 0 ]]; then
        RESULTS+=("✅ $name")
    else
        RESULTS+=("❌ $name (mã thoát $code)")
        FAILED=1
    fi
}

# Backend chạy trong container, mount code hiện tại (không cần build lại image để test).
backend() {
    docker compose run --rm --quiet-pull -v "$ROOT/backend:/app" backend "$@"
}

frontend_install() (
    cd "$ROOT/frontend"
    [[ -d node_modules ]] || npm ci --no-audit --no-fund "${NPM_CACHE_ARGS[@]}"
)

agent_env() (
    cd "$ROOT/mac-agent"
    if [[ ! -x .venv/bin/python ]]; then
        "$AGENT_PYTHON" -m venv .venv
        .venv/bin/pip install --quiet --disable-pip-version-check \
            "pyobjc-framework-EventKit>=10.3" "requests>=2.32" "pytest>=8" "ruff>=0.5"
    fi
)

agent_pytest() (
    cd "$ROOT/mac-agent"
    local code=0
    .venv/bin/python -m pytest -q || code=$?
    # Mã 5 = chưa có test nào (agent được viết ở User Story 7) → không tính là lỗi.
    [[ $code -eq 0 || $code -eq 5 ]]
)

docker compose up -d --wait db >/dev/null

step "Backend: ruff check" backend ruff check .
step "Backend: ruff format --check" backend ruff format --check .
step "Backend: pytest" backend pytest -q
if $RUN_OCR; then
    step "Backend: pytest -m ocr" backend pytest -q -m ocr
fi

step "Frontend: cài gói" frontend_install
step "Frontend: lint" bash -c "cd '$ROOT/frontend' && npm run --silent lint"
step "Frontend: test" bash -c "cd '$ROOT/frontend' && npm test --silent"

step "Agent: môi trường Python 3.11" agent_env
step "Agent: ruff" bash -c "cd '$ROOT/mac-agent' && .venv/bin/ruff check . && .venv/bin/ruff format --check ."
step "Agent: pytest" agent_pytest
step "Scripts: ruff" bash -c "cd '$ROOT' && mac-agent/.venv/bin/ruff check --config backend/pyproject.toml scripts && mac-agent/.venv/bin/ruff format --check --config backend/pyproject.toml scripts"

desktop_cargo_test() (
    [[ -d "$HOME/.cargo/bin" ]] && export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v cargo >/dev/null 2>&1; then
        echo "⚠️ Bỏ qua: chưa cài Rust"
        return 0
    fi
    cd "$ROOT/desktop/src-tauri"
    cargo test --quiet
)

step "Desktop: cargo test" desktop_cargo_test

if [[ -x "$ROOT/scripts/test-persistence.sh" ]]; then
    step "Lưu trữ qua khởi động lại" "$ROOT/scripts/test-persistence.sh"
fi

echo
echo "━━━ Tóm tắt ━━━"
printf '%s\n' "${RESULTS[@]}"
exit $FAILED
