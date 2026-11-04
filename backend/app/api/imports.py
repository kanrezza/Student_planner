"""/api/imports — nhập lịch học và lịch thi từ ảnh (FR-028 đến FR-035, FR-059 đến FR-062)."""

from flask import Blueprint, request

from app.api.errors import ApiError
from app.config import MAX_IMAGE_BYTES
from app.schemas.imports import CommitIn
from app.services import imports as service

bp = Blueprint("imports", __name__)


@bp.post("/imports/recognize")
def recognize():
    """Nhận ảnh qua multipart, nhận diện trong bộ nhớ; không `save()`, không file tạm, không DB."""
    if request.content_length and request.content_length > MAX_IMAGE_BYTES + 1024 * 1024:
        raise ApiError(413, "image_too_large", "Ảnh vượt quá 20 MB")
    upload = request.files.get("image")
    if upload is None:
        raise ApiError(400, "validation_error", "Thiếu ảnh", {"image": "Hãy chọn một ảnh"})
    data = upload.stream.read(MAX_IMAGE_BYTES + 1)
    return service.recognize(data, request.args.get("kind") or None)


@bp.post("/imports/commit")
def commit():
    payload = CommitIn.model_validate(request.get_json(silent=True) or {})
    return service.commit(payload)
