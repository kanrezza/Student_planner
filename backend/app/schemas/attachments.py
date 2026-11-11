"""Dữ liệu vào/ra của API file đính kèm (feature 005, contracts/rest-api.md)."""

from pydantic import Field

from app.lib.timeutil import iso
from app.schemas.common import ApiModel
from app.services import attachments as service
from app.services import attachments_store as store


class AttachmentRename(ApiModel):
    display_name: str = Field(min_length=1, max_length=255)


def serialize_attachment(attachment) -> dict:
    blob = attachment.blob
    owner_type, owner_id = service.owner_of(attachment)
    return {
        "id": attachment.id,
        "display_name": attachment.display_name,
        "size": blob.size,
        "mime_type": blob.mime_type,
        "preview": store.preview_kind(blob.mime_type),
        "is_executable": blob.is_executable,
        "created_at": iso(attachment.created_at),
        "owner": {
            "type": owner_type,
            "id": owner_id,
            "title": service.owner_title(attachment),
        },
        "content_url": f"/api/attachments/{attachment.id}/content",
        "download_url": f"/api/attachments/{attachment.id}/download",
    }
