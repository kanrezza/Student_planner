"""Gắn nhãn cho task, môn học, buổi học theo thứ tự (`position`) — dùng chung cho mọi loại."""

from sqlalchemy import delete, select

from app.api.errors import ApiError
from app.extensions import db
from app.models import Tag


def replace_tag_links(link_model, owner_field: str, owner_id: int, tag_ids: list[int]) -> None:
    """Thay toàn bộ nhãn của một đối tượng; thứ tự trong `tag_ids` là thứ tự gắn (FR-044)."""
    tag_ids = list(dict.fromkeys(tag_ids))  # bỏ trùng, giữ thứ tự
    if tag_ids:
        found = set(db.session.scalars(select(Tag.id).where(Tag.id.in_(tag_ids))))
        if missing := [t for t in tag_ids if t not in found]:
            raise ApiError(
                400,
                "validation_error",
                "Dữ liệu chưa hợp lệ",
                fields={"tag_ids": f"Nhãn không tồn tại: {', '.join(map(str, missing))}"},
            )
    db.session.execute(delete(link_model).where(getattr(link_model, owner_field) == owner_id))
    for position, tag_id in enumerate(tag_ids):
        db.session.add(
            link_model(**{owner_field: owner_id, "tag_id": tag_id, "position": position})
        )


def serialize_tags(tags) -> list[dict]:
    return [
        {"id": t.id, "name": t.name, "color": t.color, "system_key": t.system_key} for t in tags
    ]
