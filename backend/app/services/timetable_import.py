"""Nhập học kỳ từ PDF thời khoá biểu: xem trước (không ghi gì) và lưu (một transaction).

Chỉ đọc trong bộ nhớ, không file tạm, không log nội dung file (R6, SC-006).
"""

from sqlalchemy import func, select

from app.api.errors import ApiError
from app.extensions import db
from app.lib import timeutil
from app.models import ClassSession, Semester, Shift, Subject
from app.pdfimport.layout import parse_table
from app.pdfimport.preview import PreviewContext, build_timetable_preview, match_existing
from app.pdfimport.reader import PdfImportError, read_pdf
from app.schemas.timetable_import import TimetableCommitIn
from app.services import auto_deadlines
from app.services import canonical_names as canonical_service
from app.services import periods as periods_service
from app.services import semesters as semester_service
from app.services import subjects as subject_service


def _context() -> PreviewContext:
    shifts = list(db.session.scalars(select(Shift).order_by(Shift.position)))
    return PreviewContext(
        shifts=shifts,
        periods=periods_service.load_periods(),
        semesters=semester_service.all_semesters(),
        existing_subjects=list(db.session.scalars(select(Subject))),
    )


def preview(data: bytes) -> dict:
    """Đọc PDF và trả bản xem trước; lỗi đọc đổi thành `ApiError` đúng mã của contract."""
    try:
        table = parse_table(read_pdf(data))
        return build_timetable_preview(table.rows, table.semester_line, _context())
    except PdfImportError as err:
        raise ApiError(err.status, err.code, err.message) from None


def _apply_semester(choice) -> Semester:
    """Dùng, mở rộng hoặc tạo học kỳ — chưa commit (cùng transaction với việc tạo môn)."""
    if choice.choice == "use":
        return semester_service.get_semester(choice.semester_id)
    if choice.choice == "extend":
        semester = semester_service.get_semester(choice.semester_id)
        start = min(semester.start_date, choice.start_date)
        end = max(semester.end_date, choice.end_date)
        semester_service._check_overlap(start, end, exclude_id=semester.id)
        semester.start_date, semester.end_date = start, end
        db.session.flush()
        return semester
    semester_service._check_overlap(choice.start_date, choice.end_date)
    semester = Semester(name=choice.name, start_date=choice.start_date, end_date=choice.end_date)
    db.session.add(semester)
    db.session.flush()
    return semester


def _save_periods(rules) -> None:
    """Quy tắc có giờ nhập tay cho khoảng tiết chưa có giờ → ghi vào bảng tiết (FR-015)."""
    for rule in rules:
        if rule.save_periods and rule.period_from and rule.period_to and not rule.shift:
            if rule.start_time and rule.end_time:
                periods_service.save_manual_periods(
                    rule.period_from, rule.period_to, rule.start_time, rule.end_time
                )


def _format_dates(sessions) -> str:
    return ", ".join(f"{d.day:02d}/{d.month:02d}" for d in sorted(s.date for s in sessions))


def commit(payload: TimetableCommitIn) -> dict:
    """Lưu phần đã chọn. Lỗi ở bất kỳ môn/quy tắc nào → không lưu gì (FR-025).

    Server tự tìm môn đã có theo khoá R9 (không tin client): môn đã có được cập nhật, môn mới được
    tạo; môn không có trong file không bị đụng tới.
    """
    try:
        semester = _apply_semester(payload.semester)
        existing = list(
            db.session.scalars(select(Subject).where(Subject.semester_id == semester.id))
        )
        new_items: list[dict] = []
        new_positions: list[int] = []
        updates = []
        warnings: list[dict] = []
        today = timeutil.today()
        for index, subject in enumerate(payload.subjects):
            item = subject.model_dump(exclude={"existing_subject_id"})
            item["schedules"] = [
                {k: v for k, v in rule.items() if k != "save_periods"} for rule in item["schedules"]
            ]
            _save_periods(subject.schedules)
            match = match_existing(item, existing)
            if subject.existing_subject_id is not None and (
                match is None or match.id != subject.existing_subject_id
            ):
                raise ApiError(
                    400,
                    "validation_error",
                    "Dữ liệu chưa hợp lệ",
                    {f"subjects[{index}].existing_subject_id": "Môn này không khớp với môn đã có"},
                )
            if match is not None:
                result = subject_service.update_from_import(
                    match, item, today, prefix=f"subjects[{index}]."
                )
                updates.append(result)
                if result.kept:
                    warnings.append(
                        {
                            "code": "kept_exception_sessions",
                            "message": f"Giữ lại các buổi đã huỷ hoặc sửa riêng của “{match.name}” "
                            f"nằm ngoài lịch mới: {_format_dates(result.kept)}",
                        }
                    )
            else:
                item["semester_id"] = semester.id
                new_items.append(item)
                new_positions.append(index)
        created, create_warnings = subject_service.create_many(
            new_items, row_name="subjects", index_map=new_positions
        )
        created_sessions = db.session.scalar(
            select(func.count())
            .select_from(ClassSession)
            .where(ClassSession.subject_id.in_([s.id for s in created]))
        )
    except Exception:
        db.session.rollback()
        raise
    canonical_service.record([(s.name, s.course_code) for s in payload.subjects])
    auto_deadlines.reconcile(subject_ids=[u.subject.id for u in updates])
    db.session.commit()
    return {
        "semester_id": semester.id,
        "created_subjects": len(created),
        "updated_subjects": len(updates),
        "created_sessions": (created_sessions or 0) + sum(u.created for u in updates),
        "updated_sessions": sum(u.updated for u in updates),
        "skipped_sessions": sum(u.skipped for u in updates),
        "kept_exception_sessions": sum(len(u.kept) for u in updates),
        "warnings": warnings + create_warnings,
    }
