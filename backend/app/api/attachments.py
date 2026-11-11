"""/api/attachments — file đính kèm của task, môn học, buổi học, buổi thi (feature 005)."""

from flask import Blueprint, Response, request, send_file

from app.api.errors import ApiError
from app.schemas.attachments import AttachmentRename, serialize_attachment
from app.services import attachments as service
from app.services import attachments_store as store

bp = Blueprint("attachments", __name__)

MAX_REQUEST_BYTES = 510 * service.MIB  # trần 500 MB của cài đặt + phần đầu multipart


def _required_args() -> tuple[str, int]:
    owner_type = request.values.get("owner_type")
    owner_id = request.values.get("owner_id", type=int)
    if not owner_type or owner_id is None:
        raise ApiError(
            400,
            "validation_error",
            "Thiếu nơi đính kèm",
            {"owner_type": "Bắt buộc", "owner_id": "Bắt buộc"},
        )
    return owner_type, owner_id


@bp.get("/attachments")
def list_attachments():
    owner_type, owner_id = _required_args()
    return [serialize_attachment(a) for a in service.list_for(owner_type, owner_id)]


@bp.get("/attachments/stats")
def stats():
    result = service.stats()
    return {**result, "largest": [serialize_attachment(a) for a in result["largest"]]}


@bp.get("/attachments/<int:attachment_id>")
def get_attachment(attachment_id: int):
    return serialize_attachment(service.get(attachment_id))


@bp.post("/attachments")
def upload():
    request.max_content_length = MAX_REQUEST_BYTES
    owner_type, owner_id = _required_args()
    service.owner_object(owner_type, owner_id)
    files = request.files.getlist("file")
    if not files:
        raise ApiError(400, "validation_error", "Thiếu file", {"file": "Hãy chọn file để đính kèm"})
    created, errors, first_status = [], [], None
    for upload_file in files:
        name = upload_file.filename or "file"
        try:
            created.append(
                service.create_from_stream(owner_type, owner_id, name, upload_file.stream)
            )
        except store.FileTooLarge:
            limit = service.settings().attachment_max_mb
            message = f"File vượt quá {limit} MB (giới hạn trong Cài đặt → File đính kèm)"
            errors.append({"name": name, "code": "file_too_large", "message": message})
            first_status = first_status or 413
        except store.DiskFull:
            errors.append({"name": name, "code": "disk_full", "message": "Ổ đĩa không đủ chỗ"})
            first_status = first_status or 507
        except ApiError as error:
            errors.append({"name": name, "code": error.code, "message": error.message})
            first_status = first_status or error.status
    body = {"attachments": [serialize_attachment(a) for a in created], "errors": errors}
    if not created and first_status:
        return body, first_status
    return body, 201


@bp.patch("/attachments/<int:attachment_id>")
def rename(attachment_id: int):
    data = AttachmentRename.model_validate(request.get_json(silent=True) or {})
    return serialize_attachment(service.rename(attachment_id, data.display_name))


@bp.delete("/attachments/<int:attachment_id>")
def delete(attachment_id: int):
    service.delete(attachment_id)
    return "", 204


def _file_response(attachment_id: int, as_attachment: bool) -> Response:
    attachment = service.get(attachment_id)
    blob = attachment.blob
    try:
        path = store.open_blob(blob.sha256)
    except FileNotFoundError:
        raise ApiError(404, "attachment_missing", "File bị thiếu trong kho lưu trữ") from None
    inline = not as_attachment and store.preview_kind(blob.mime_type) is not None
    response = send_file(
        path,
        mimetype=blob.mime_type if inline else "application/octet-stream",
        as_attachment=not inline,
        download_name=attachment.display_name,
        conditional=True,
        etag=blob.sha256,
        max_age=0,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "sandbox; default-src 'none'; img-src 'self'; object-src 'self'; style-src 'unsafe-inline'"
    )
    return response


@bp.get("/attachments/<int:attachment_id>/content")
def content(attachment_id: int):
    return _file_response(attachment_id, as_attachment=False)


@bp.get("/attachments/<int:attachment_id>/download")
def download(attachment_id: int):
    return _file_response(attachment_id, as_attachment=True)
