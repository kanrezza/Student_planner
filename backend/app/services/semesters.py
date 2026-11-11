"""Học kỳ (FR-036, FR-037): không chồng lấn; thu hẹp ngày thì môn học phải được xử lý trước."""

from datetime import date

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib import timeutil
from app.models import Semester, Subject
from app.services import auto_deadlines
from app.services.revision import bump_revision


def _fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def current_semester_of(semesters: list[Semester], today: date) -> Semester | None:
    """Học kỳ chứa hôm nay; nếu không có thì học kỳ sắp tới gần nhất (hàm thuần)."""
    for s in semesters:
        if s.start_date <= today <= s.end_date:
            return s
    upcoming = [s for s in semesters if s.start_date > today]
    return min(upcoming, key=lambda s: s.start_date, default=None)


def all_semesters() -> list[Semester]:
    return list(db.session.scalars(select(Semester).order_by(Semester.start_date)))


def current_semester() -> Semester | None:
    return current_semester_of(all_semesters(), timeutil.today())


def get_semester(semester_id: int) -> Semester:
    semester = db.session.get(Semester, semester_id)
    if semester is None:
        raise not_found("Không tìm thấy học kỳ")
    return semester


def _check_overlap(start: date, end: date, exclude_id: int | None = None) -> None:
    for other in all_semesters():
        if other.id != exclude_id and other.start_date <= end and start <= other.end_date:
            raise ApiError(
                400,
                "validation_error",
                "Dữ liệu chưa hợp lệ",
                {
                    "start_date": f"Trùng thời gian với học kỳ “{other.name}” "
                    f"({_fmt(other.start_date)} – {_fmt(other.end_date)})"
                },
            )


def create_semester(name: str, start: date, end: date) -> Semester:
    _check_overlap(start, end)
    semester = Semester(name=name, start_date=start, end_date=end)
    db.session.add(semester)
    bump_revision(db.session)
    db.session.commit()
    return semester


def update_semester(semester_id: int, changes: dict, clamp_subjects: bool) -> Semester:
    """Thu hẹp ngày làm môn ra ngoài khoảng → 409 kèm danh sách môn, trừ khi `clamp_subjects`.

    Khi thu hẹp: ngày của môn được cắt vào khoảng mới; môn nằm hẳn ngoài khoảng mới bị xoá.
    """
    from app.services import subjects as subject_service  # tránh import vòng

    semester = get_semester(semester_id)
    start = changes.get("start_date") or semester.start_date
    end = changes.get("end_date") or semester.end_date
    if end < start:
        raise ApiError(
            400,
            "validation_error",
            "Dữ liệu chưa hợp lệ",
            {"end_date": "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"},
        )
    _check_overlap(start, end, exclude_id=semester_id)

    affected = [
        s
        for s in db.session.scalars(select(Subject).where(Subject.semester_id == semester_id))
        if s.date_span and (s.date_span[0] < start or s.date_span[1] > end)
    ]
    if affected and not clamp_subjects:
        raise ApiError(
            409,
            "conflict",
            "Một số môn học nằm ngoài khoảng ngày mới của học kỳ",
            details={
                "subjects": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "start_date": s.date_span[0].isoformat(),
                        "end_date": s.date_span[1].isoformat(),
                        "will_be_deleted": _all_outside(s, start, end),
                    }
                    for s in affected
                ]
            },
        )

    if changes.get("name"):
        semester.name = changes["name"]
    semester.start_date, semester.end_date = start, end
    kept = []
    for subject in affected:
        if _all_outside(subject, start, end):
            auto_deadlines.drop_for_subjects([subject.id])
            db.session.delete(subject)
            continue
        kept.append(subject.id)
        for rule in list(subject.schedules):
            if rule.end_date < start or rule.start_date > end:
                for session in subject.sessions:
                    if session.schedule_id == rule.id:
                        session.schedule_id = None
                subject.schedules.remove(rule)  # lịch nằm hẳn ngoài học kỳ mới
                continue
            rule.start_date = max(rule.start_date, start)
            rule.end_date = min(rule.end_date, end)
        db.session.flush()
        subject_service.regenerate_sessions(subject, force=True)
    auto_deadlines.reconcile(subject_ids=kept)
    bump_revision(db.session)
    db.session.commit()
    return semester


def _all_outside(subject, start: date, end: date) -> bool:
    """Mọi lịch học của môn nằm hẳn ngoài khoảng [start, end]."""
    return all(rule.end_date < start or rule.start_date > end for rule in subject.schedules)


def delete_semester(semester_id: int, confirm: bool) -> None:
    semester = get_semester(semester_id)
    count = len(semester.subjects)
    if count and not confirm:
        raise ApiError(
            409,
            "conflict",
            f"Xoá học kỳ sẽ xoá {count} môn học cùng mọi buổi học",
            details={"subject_count": count},
        )
    auto_deadlines.drop_for_subjects(auto_deadlines.subject_ids_of_semester(semester_id))
    db.session.delete(semester)
    bump_revision(db.session)
    db.session.commit()
