"""Nhãn có màu (FR-042 đến FR-046). Nhãn hệ thống (`system_key`) chỉ được đổi màu."""

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.text import ci_key
from app.models import Subject, SubjectTag, Tag
from app.services import auto_deadlines
from app.services.colors import is_palette_color, next_color
from app.services.revision import bump_revision
from app.services.tag_links import replace_tag_links


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def list_tags() -> list[Tag]:
    return list(db.session.scalars(select(Tag).order_by(Tag.id)))


def get_tag(tag_id: int) -> Tag:
    tag = db.session.get(Tag, tag_id)
    if tag is None:
        raise not_found("Không tìm thấy nhãn")
    return tag


def _check_name(name: str, exclude_id: int | None = None) -> None:
    for other in list_tags():
        if other.id != exclude_id and ci_key(other.name) == ci_key(name):
            raise _invalid("name", "Đã có nhãn tên này")


def _check_color(color: str) -> None:
    if not is_palette_color(color):
        raise _invalid("color", "Màu không hợp lệ")


def create_tag(name: str, color: str | None) -> Tag:
    _check_name(name)
    color = color or next_color([t.color for t in list_tags()])
    _check_color(color)
    tag = Tag(name=name, color=color)
    db.session.add(tag)
    db.session.commit()
    return tag


def update_tag(tag_id: int, changes: dict) -> Tag:
    tag = get_tag(tag_id)
    if changes.get("name") is not None and changes["name"] != tag.name:
        if tag.system_key:
            raise _invalid("name", "Không đổi được tên nhãn hệ thống")
        _check_name(changes["name"], exclude_id=tag_id)
        tag.name = changes["name"]
    if changes.get("color") is not None:
        _check_color(changes["color"])
        tag.color = changes["color"]
    db.session.commit()
    return tag


def delete_tag(tag_id: int) -> None:
    """Gỡ nhãn khỏi mọi mục (ON DELETE CASCADE trên các bảng nối)."""
    tag = get_tag(tag_id)
    if tag.system_key:
        raise ApiError(400, "system_tag", "Không xoá được nhãn hệ thống")
    db.session.delete(tag)
    auto_deadlines.reconcile(all_future=True)
    bump_revision(db.session)
    db.session.commit()


def set_subject_tags(subject_id: int, tag_ids: list[int]) -> Subject:
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        raise not_found("Không tìm thấy môn học")
    replace_tag_links(SubjectTag, "subject_id", subject.id, tag_ids)
    auto_deadlines.reconcile(subject_ids=[subject_id])
    bump_revision(db.session)
    db.session.commit()
    db.session.expire(subject, ["tag_links"])
    return subject
