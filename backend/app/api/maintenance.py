"""Chế độ bảo trì khi đang khôi phục dữ liệu (feature 003, research R8).

Trong lúc `pg_restore` chạy, mọi API khác trả 503 `restoring` (không ai ghi được vào dữ liệu).
"""

from flask import Flask, request

from app.api.errors import ApiError
from app.services import backup

# (phương thức, đường dẫn) vẫn được phục vụ khi đang khôi phục.
_ALLOWED_PATHS = {
    ("GET", "/api/health"),
    ("GET", "/api/backup/status"),
    ("PUT", "/api/backup/agent-report"),
    ("POST", "/api/backup/restore"),
}


def _allowed(method: str, path: str) -> bool:
    if (method, path) in _ALLOWED_PATHS:
        return True
    return method == "PUT" and path.startswith("/api/backup/jobs/")


def register(app: Flask) -> None:
    @app.before_request
    def block_while_restoring():
        if backup.is_restoring() and not _allowed(request.method, request.path):
            return ApiError(503, "restoring", "Đang khôi phục dữ liệu…").to_response()
        return None
