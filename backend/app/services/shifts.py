"""Ca học (FR-038 đến FR-041). Hàm thuần ở đầu file; hàm ghi dữ liệu gọi `bump_revision`."""

from datetime import time

from sqlalchemy import func, or_, select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.text import ci_key
from app.models import Shift, Subject
from app.services.revision import bump_revision

TOLERANCE_MINUTES = 5


# ---- Hàm thuần ------------------------------------------------------------------------------


def resolve_range(first, last) -> tuple[time, time]:
    """Giờ của dãy ca: bắt đầu của ca đầu → kết thúc của ca cuối."""
    return first.start_time, last.end_time


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def match_shift_range(
    start: time, end: time, shifts, tolerance_min: int = TOLERANCE_MINUTES
) -> tuple[int, int] | None:
    """Tìm một ca hoặc dãy ca liền nhau có giờ khớp (lệch tối đa `tolerance_min` phút) (FR-041).

    Trả (id ca đầu, id ca cuối) hoặc None.
    """
    ordered = sorted(shifts, key=lambda s: s.position)
    for i, first in enumerate(ordered):
        if abs(_minutes(first.start_time) - _minutes(start)) > tolerance_min:
            continue
        for last in ordered[i:]:
            if abs(_minutes(last.end_time) - _minutes(end)) <= tolerance_min:
                return first.id, last.id
    return None


def shift_label(start_shift, end_shift) -> str | None:
    """ "Ca 1" hoặc "Ca 1–2" (bỏ tiền tố chung "Ca " ở ca cuối)."""
    if start_shift is None or end_shift is None:
        return None
    if start_shift.id == end_shift.id:
        return start_shift.name
    end_name = end_shift.name
    if start_shift.name.startswith("Ca ") and end_name.startswith("Ca "):
        end_name = end_name.removeprefix("Ca ")
    return f"{start_shift.name}–{end_name}"


# ---- Truy vấn và ghi dữ liệu --------------------------------------------------------------------


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def list_shifts() -> list[Shift]:
    return list(db.session.scalars(select(Shift).order_by(Shift.position)))


def get_shift(shift_id: int) -> Shift:
    shift = db.session.get(Shift, shift_id)
    if shift is None:
        raise not_found("Không tìm thấy ca học")
    return shift


def _subjects_using(shift_id: int) -> list[Subject]:
    return list(
        db.session.scalars(
            select(Subject).where(
                or_(Subject.start_shift_id == shift_id, Subject.end_shift_id == shift_id)
            )
        )
    )


def _check(name: str | None, start: time, end: time, exclude_id: int | None = None) -> None:
    if end <= start:
        raise _invalid("end_time", "Giờ kết thúc phải sau giờ bắt đầu")
    if name is not None:
        for other in list_shifts():
            if other.id != exclude_id and ci_key(other.name) == ci_key(name):
                raise _invalid("name", "Đã có ca học tên này")


def create_shift(name: str, start: time, end: time) -> Shift:
    _check(name, start, end)
    position = (db.session.scalar(select(func.max(Shift.position))) or 0) + 1
    shift = Shift(name=name, start_time=start, end_time=end, position=position)
    db.session.add(shift)
    db.session.commit()
    return shift


def update_shift(shift_id: int, changes: dict, confirm: bool) -> Shift:
    """Đổi giờ ca đang được dùng: cần `confirm`; các môn dùng ca cập nhật giờ và buổi học,
    trừ buổi đã sửa giờ riêng (FR-040)."""
    from app.services.subjects import regenerate_sessions  # tránh import vòng

    shift = get_shift(shift_id)
    start = changes.get("start_time") or shift.start_time
    end = changes.get("end_time") or shift.end_time
    _check(changes.get("name"), start, end, exclude_id=shift_id)

    times_changed = (start, end) != (shift.start_time, shift.end_time)
    users = _subjects_using(shift_id) if times_changed else []
    if users and not confirm:
        raise ApiError(
            409,
            "conflict",
            f"{len(users)} môn học sẽ cập nhật theo giờ mới của ca",
            details={"subject_count": len(users)},
        )
    if changes.get("name"):
        shift.name = changes["name"]
    shift.start_time, shift.end_time = start, end
    db.session.flush()
    for subject in users:
        subject.start_time, subject.end_time = resolve_range(subject.start_shift, subject.end_shift)
        regenerate_sessions(subject)
    if times_changed:
        bump_revision(db.session)
    db.session.commit()
    return shift


def delete_shift(shift_id: int, confirm: bool) -> None:
    """Xoá ca đang được dùng: cần `confirm`; các môn giữ giờ hiện tại, chuyển sang giờ tuỳ chỉnh."""
    shift = get_shift(shift_id)
    users = _subjects_using(shift_id)
    if users and not confirm:
        raise ApiError(
            409,
            "conflict",
            f"{len(users)} môn học sẽ chuyển sang giờ tuỳ chỉnh",
            details={"subject_count": len(users)},
        )
    for subject in users:
        subject.start_shift_id = None
        subject.end_shift_id = None
    db.session.flush()
    db.session.delete(shift)
    db.session.commit()
