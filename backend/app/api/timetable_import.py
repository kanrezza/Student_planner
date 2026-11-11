"""/api/imports/timetable-pdf — nhập học kỳ từ PDF thời khoá biểu chính thức (feature 004)."""

from flask import Blueprint, request

from app.api.errors import ApiError
from app.config import MAX_IMAGE_BYTES
from app.schemas.timetable_import import TimetableCommitIn
from app.services import timetable_import as service

bp = Blueprint("timetable_import", __name__)


@bp.post("/imports/timetable-pdf/preview")
def preview():
    """Nhận PDF qua multipart, đọc trong bộ nhớ; không `save()`, không file tạm, không ghi DB."""
    if request.content_length and request.content_length > MAX_IMAGE_BYTES + 1024 * 1024:
        raise ApiError(413, "file_too_large", "File vượt quá 20 MB")
    upload = request.files.get("file")
    if upload is None:
        raise ApiError(400, "validation_error", "Thiếu file", {"file": "Hãy chọn một file PDF"})
    data = upload.stream.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ApiError(413, "file_too_large", "File vượt quá 20 MB")
    return service.preview(data)


@bp.post("/imports/timetable-pdf/commit")
def commit():
    payload = TimetableCommitIn.model_validate(request.get_json(silent=True) or {})
    return service.commit(payload)
