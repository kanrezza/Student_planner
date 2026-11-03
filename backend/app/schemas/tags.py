from pydantic import Field

from app.schemas.common import ApiModel, VietnameseText


class TagIn(ApiModel):
    name: VietnameseText = Field(min_length=1, max_length=50)
    color: str | None = None


class TagPatch(ApiModel):
    name: VietnameseText | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = None


class TagIdsIn(ApiModel):
    """Thứ tự trong mảng là thứ tự gắn: nhãn đầu tiên quyết định màu hiển thị (FR-044)."""

    tag_ids: list[int]


def serialize_tag(tag) -> dict:
    return {"id": tag.id, "name": tag.name, "color": tag.color, "system_key": tag.system_key}
