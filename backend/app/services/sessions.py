"""Sửa hoặc huỷ một buổi học riêng lẻ (FR-011, FR-012): không ảnh hưởng buổi khác của môn."""

from sqlalchemy import select

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


def _validation_error(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def update_session(session_id: int, changes: dict) -> tuple[ClassSession, list[dict]]:
    """Đổi ngày (dời buổi), giờ (`time_overridden`) và/hoặc phòng (`room_overridden`) của buổi.

    Dời ngày (feature 002 FR-028, research R8): đặt `original_date` nếu đang trống; dời về đúng ngày
    gốc thì xoá `original_date`. Trả `(buổi, cảnh báo)`; ngoài học kỳ → cảnh báo `outside_semester`.
    """
    session = get_session(session_id)
    warnings: list[dict] = []
    new_date = changes.get("date", session.date)
    moving = new_date != session.date
    if moving or "start_time" in changes or "end_time" in changes:
        start = changes.get("start_time") or session.start_at.astimezone(TZ).time()
        end = changes.get("end_time") or session.end_at.astimezone(TZ).time()
        if end <= start:
            raise _validation_error("end_time", "Giờ kết thúc phải sau giờ bắt đầu")
        new_start = combine(new_date, start)
        taken = db.session.scalar(
            select(ClassSession.id).where(
                ClassSession.subject_id == session.subject_id,
                ClassSession.date == new_date,
                ClassSession.start_at == new_start,
                ClassSession.id != session.id,
            )
        )
        if taken is not None:
            raise _validation_error("date", "Môn này đã có buổi học vào ngày và giờ đó")
        time_changed = (start, end) != (
            session.start_at.astimezone(TZ).time(),
            session.end_at.astimezone(TZ).time(),
        )
        if moving:
            if session.original_date is None:
                session.original_date = session.date
            elif session.original_date == new_date:
                session.original_date = None  # dời về đúng ngày gốc
            session.date = new_date
        session.start_at = new_start
        session.end_at = combine(new_date, end)
        if time_changed:
            session.time_overridden = True
        semester = session.subject.semester
        if moving and not semester.start_date <= new_date <= semester.end_date:
            warnings.append(
                {"code": "outside_semester", "message": "Ngày mới nằm ngoài học kỳ của môn này"}
            )
    if "room" in changes:
        session.room = changes["room"]
        session.room_overridden = True
    if "important_override" in changes:
        session.important_override = changes["important_override"]
    auto_deadlines.reconcile(session_ids=[session_id])
    bump_revision(db.session)
    db.session.commit()
    return session, warnings


def set_session_tags(session_id: int, tag_ids: list[int]) -> ClassSession:
    """Nhãn riêng của buổi, cộng thêm vào nhãn của môn (FR-043)."""
    session = get_session(session_id)
    replace_tag_links(SessionTag, "session_id", session.id, tag_ids)
    auto_deadlines.reconcile(session_ids=[session_id])
    bump_revision(db.session)
    db.session.commit()
    db.session.expire(session, ["tag_links"])
    return session
