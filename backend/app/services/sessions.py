"""Sửa hoặc huỷ một buổi học riêng lẻ (FR-011, FR-012): không ảnh hưởng buổi khác của môn."""

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, SessionTag
from app.services import auto_deadlines
from app.services.revision import bump_revision
from app.services.tag_links import replace_tag_links


def get_session(session_id: int) -> ClassSession:
    session = db.session.get(ClassSession, session_id)
    if session is None:
        raise not_found("Không tìm thấy buổi học")
    return session


def set_cancelled(session_id: int, cancelled: bool) -> ClassSession:
    """Huỷ hoặc khôi phục; khôi phục giữ nguyên giờ/phòng đã sửa riêng."""
    session = get_session(session_id)
    session.is_cancelled = cancelled
    auto_deadlines.reconcile(session_ids=[session_id])
    bump_revision(db.session)
    db.session.commit()
    return session


def update_session(session_id: int, changes: dict) -> ClassSession:
    """Đổi giờ (đặt `time_overridden`) và/hoặc phòng (đặt `room_overridden`) cho riêng buổi này."""
    session = get_session(session_id)
    if "start_time" in changes or "end_time" in changes:
        start = changes.get("start_time") or session.start_at.astimezone(TZ).time()
        end = changes.get("end_time") or session.end_at.astimezone(TZ).time()
        if end <= start:
            raise ApiError(
                400,
                "validation_error",
                "Dữ liệu chưa hợp lệ",
                {"end_time": "Giờ kết thúc phải sau giờ bắt đầu"},
            )
        session.start_at = combine(session.date, start)
        session.end_at = combine(session.date, end)
        session.time_overridden = True
    if "room" in changes:
        session.room = changes["room"]
        session.room_overridden = True
    auto_deadlines.reconcile(session_ids=[session_id])
    bump_revision(db.session)
    db.session.commit()
    return session


def set_session_tags(session_id: int, tag_ids: list[int]) -> ClassSession:
    """Nhãn riêng của buổi, cộng thêm vào nhãn của môn (FR-043)."""
    session = get_session(session_id)
    replace_tag_links(SessionTag, "session_id", session.id, tag_ids)
    auto_deadlines.reconcile(session_ids=[session_id])
    bump_revision(db.session)
    db.session.commit()
    db.session.expire(session, ["tag_links"])
    return session
