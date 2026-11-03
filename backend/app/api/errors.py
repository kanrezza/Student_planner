"""Định dạng lỗi chung của API (contracts/rest-api.md):

{"error": {"code": "...", "message": "<tiếng Việt>", "fields": {...}?, "details": {...}?}}
"""

import logging

from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.schemas.common import vi_error_messages

log = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields
        self.details = details

    def to_response(self):
        body = {"code": self.code, "message": self.message}
        if self.fields:
            body["fields"] = self.fields
        if self.details is not None:
            body["details"] = self.details
        return jsonify({"error": body}), self.status


def not_found(what: str = "Không tìm thấy dữ liệu") -> ApiError:
    return ApiError(404, "not_found", what)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return err.to_response()

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        fields = vi_error_messages(err.errors())
        return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", fields=fields).to_response()

    @app.errorhandler(404)
    def handle_404(_err):
        return not_found("Không tìm thấy đường dẫn này").to_response()

    @app.errorhandler(405)
    def handle_405(_err):
        return ApiError(405, "method_not_allowed", "Phương thức không được hỗ trợ").to_response()

    @app.errorhandler(413)
    def handle_413(_err):
        return ApiError(413, "image_too_large", "Ảnh vượt quá 20 MB").to_response()

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        if isinstance(err, HTTPException):
            return ApiError(err.code or 500, "http_error", err.description or "").to_response()
        log.exception("Lỗi không mong đợi")
        return ApiError(500, "internal_error", "Đã có lỗi xảy ra, vui lòng thử lại").to_response()
