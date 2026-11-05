"""Nghiệp vụ task (FR-001 đến FR-006). Hàm thuần ở đầu file; hàm ghi dữ liệu gọi `bump_revision`."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import ColumnElement, Select, and_, delete, func, or_, select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib import timeutil
from app.lib.timeutil import combine
from app.models import ClassSession, Task, TaskList, TaskTag
from app.services.revision import bump_revision
from app.services.tag_links import replace_tag_links

END_OF_DAY = time(23, 59)
DUE_TIME_NEEDS_DATE = "Cần chọn ngày hạn chót trước khi đặt giờ"
REQUIRED = "Trường này là bắt buộc"
WORK_WINDOW_INCOMPLETE = "Cần chọn đủ ngày, giờ bắt đầu và giờ kết thúc"
WORK_END_BEFORE_START = "Giờ kết thúc phải sau giờ bắt đầu"
SMART_VIEWS = ("today", "tomorrow", "next7", "all", "completed", "trash")
TRASH_KEEP_DAYS = 30
PURGE_EVERY = timedelta(hours=1)


# ---- Hàm thuần ------------------------------------------------------------------------------


def due_at(task) -> datetime | None:
    """Hạn chót = ngày + giờ; task chỉ có ngày thì hạn là 23:59 ngày đó."""
    if task.due_date is None:
        return None
    return combine(task.due_date, task.due_time or END_OF_DAY)


def is_overdue(task, now: datetime) -> bool:
    deadline = due_at(task)
    return task.completed_at is None and deadline is not None and deadline < now


_FAR_FUTURE = combine(date(9999, 12, 31), END_OF_DAY)


def sort_key(task) -> tuple:
    """Theo hạn chót (task không hạn ở cuối), rồi mức ưu tiên Cao → Thấp (FR-005)."""
    deadline = due_at(task)
    return (deadline is None, deadline or _FAR_FUTURE, task.priority, task.id)


def work_window_error(task) -> dict[str, str] | None:
    """Lỗi theo trường của khung giờ làm (feature 002 FR-018), None nếu hợp lệ."""
    values = (task.work_date, task.work_start, task.work_end)
    if any(v is None for v in values) and any(v is not None for v in values):
        return {"work_date": WORK_WINDOW_INCOMPLETE}
    if task.work_end is not None and task.work_end <= task.work_start:
        return {"work_end": WORK_END_BEFORE_START}
    return None


def task_warnings(task) -> list[dict]:
    """Cảnh báo không chặn việc lưu (data-model 002)."""
    if task.work_date and task.due_date and task.work_date > task.due_date:
        return [{"code": "work_after_due", "message": "Khung giờ làm sau hạn chót"}]
    return []


# ---- Truy vấn ---------------------------------------------------------------------------------


def active_tasks() -> Select:
    """Truy vấn task đang dùng (không ở Thùng rác). Mọi chỗ đọc task cho người dùng hay cho việc
    đồng bộ PHẢI bắt đầu từ đây (feature 002 FR-030)."""
    return select(Task).where(Task.deleted_at.is_(None))


def get_task(task_id: int, include_trashed: bool = False) -> Task:
    task = db.session.get(Task, task_id)
    if task is None or (task.deleted_at is not None and not include_trashed):
        raise not_found("Không tìm thấy công việc")
    return task


def _has_any_tag(tag_ids: list[int]) -> ColumnElement:
    return Task.id.in_(select(TaskTag.task_id).where(TaskTag.tag_id.in_(tag_ids)))


def list_tasks(
    list_id: int | None = None, include_completed: bool = False, tag_ids: list[int] | None = None
) -> list[Task]:
    query = active_tasks()
    if list_id is not None:
        query = query.where(Task.list_id == list_id)
    if not include_completed:
        query = query.where(Task.completed_at.is_(None))
    if tag_ids:
        query = query.where(_has_any_tag(tag_ids))
    return sorted(db.session.scalars(query), key=sort_key)


# ---- Danh sách thông minh và số đếm (feature 002 FR-008, FR-009) -------------------------------


def _open() -> ColumnElement:
    return and_(Task.deleted_at.is_(None), Task.completed_at.is_(None))


def _view_condition(view: str, today: date) -> ColumnElement:
    """Điều kiện của view `today`/`tomorrow`/`next7`/`all` (task chưa xong, đang dùng).

    Quá hạn = hạn chót trước bây giờ; mọi task có `due_date <= hôm nay` đều thuộc Hôm nay, nên chỉ
    cần so sánh ngày.
    """
    tomorrow, last = today + timedelta(days=1), today + timedelta(days=6)
    conditions = {
        "today": or_(Task.due_date <= today, Task.work_date == today),
        "tomorrow": or_(Task.due_date == tomorrow, Task.work_date == tomorrow),
        "next7": or_(Task.due_date <= last, Task.work_date.between(today, last)),
        "all": True,
    }
    return and_(_open(), conditions[view])


def smart_view(
    view: str | None, now: datetime, list_id: int | None = None, tag_id: int | None = None
) -> list[Task]:
    if list_id is not None:
        query = select(Task).where(_open(), Task.list_id == list_id)
    elif tag_id is not None:
        query = select(Task).where(_open(), _has_any_tag([tag_id]))
    elif view == "completed":
        query = active_tasks().where(Task.completed_at.is_not(None))
        return list(db.session.scalars(query.order_by(Task.completed_at.desc(), Task.id.desc())))
    elif view == "trash":
        purge_expired_trash(now)
        query = select(Task).where(Task.deleted_at.is_not(None))
        return list(db.session.scalars(query.order_by(Task.deleted_at.desc(), Task.id.desc())))
    else:
        query = select(Task).where(_view_condition(view, now.date()))
    return sorted(db.session.scalars(query), key=sort_key)


def counts(now: datetime) -> dict:
    """Số task chưa xong của các danh sách thông minh và từng danh sách (FR-008)."""
    purge_expired_trash(now)
    today = now.date()
    result = {
        view: db.session.scalar(select(func.count()).where(_view_condition(view, today)))
        for view in ("today", "tomorrow", "next7", "all")
    }
    per_list = db.session.execute(
        select(Task.list_id, func.count()).where(_open()).group_by(Task.list_id)
    ).all()
    result["lists"] = {str(list_id): n for list_id, n in per_list}
    return result


# ---- Ghi dữ liệu ------------------------------------------------------------------------------


def _check_list(list_id: int) -> None:
    if db.session.get(TaskList, list_id) is None:
        raise ApiError(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"list_id": "Danh sách không tồn tại"}
        )


def _check_work_window(task) -> None:
    fields = work_window_error(task)
    if fields:
        raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", fields)


def create_task(data: dict) -> Task:
    tag_ids = data.pop("tag_ids", [])
    tag_names = data.pop("tag_names", [])
    _check_list(data["list_id"])
    task = Task(**data)
    _check_work_window(task)
    db.session.add(task)
    db.session.flush()
    if tag_names:
        from app.services.tags import ensure_tags  # import muộn: tags ↔ tasks có vòng phụ thuộc

        tag_ids = [*tag_ids, *ensure_tags(tag_names)]
    replace_tag_links(TaskTag, "task_id", task.id, tag_ids)
    bump_revision(db.session)
    db.session.commit()
    return task


def update_task(task_id: int, changes: dict) -> Task:
    """`changes` chỉ chứa trường được gửi; giá trị None nghĩa là xoá (với trường cho phép)."""
    task = get_task(task_id)
    for field in ("title", "priority", "list_id"):
        if field in changes and changes[field] is None:
            raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: REQUIRED})
    if "list_id" in changes:
        _check_list(changes["list_id"])

    tag_ids = changes.pop("tag_ids", None)
    for field, value in changes.items():
        setattr(task, field, value)
    if task.due_time is not None and task.due_date is None:
        raise ApiError(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"due_time": DUE_TIME_NEEDS_DATE}
        )
    _check_work_window(task)
    if tag_ids is not None:
        replace_tag_links(TaskTag, "task_id", task.id, tag_ids)
        db.session.expire(task, ["tag_links"])
    if task.is_auto and (changes or tag_ids is not None):
        task.user_modified = True  # task tự tạo đã bị người dùng sửa → không tự cập nhật nữa
    bump_revision(db.session)
    db.session.commit()
    return task


def set_completed(task_id: int, completed: bool) -> Task:
    task = get_task(task_id)
    task.completed_at = timeutil.now() if completed else None
    bump_revision(db.session)
    db.session.commit()
    return task


# ---- Thùng rác (feature 002 FR-030, FR-031; data-model "Vòng đời Thùng rác") -------------------


def _set_auto_suppressed(task: Task, suppressed: bool) -> ClassSession | None:
    if not task.is_auto or task.source_session_id is None:
        return None
    session = db.session.get(ClassSession, task.source_session_id)
    if session is not None:
        session.auto_task_suppressed = suppressed
    return session


def move_to_trash(task: Task, now: datetime, from_list_name: str | None = None) -> None:
    """Chuyển task vào Thùng rác (không commit); task tự tạo không bị tạo lại cho buổi đó."""
    task.deleted_at = now
    if from_list_name is not None and task.trashed_from_list_name is None:
        task.trashed_from_list_name = from_list_name
    _set_auto_suppressed(task, True)


def trash_task(task_id: int) -> Task:
    task = get_task(task_id)
    move_to_trash(task, timeutil.now())
    bump_revision(db.session)
    db.session.commit()
    return task


def _trashed(task_id: int) -> Task:
    task = get_task(task_id, include_trashed=True)
    if task.deleted_at is None:
        raise not_found("Công việc không có trong Thùng rác")
    return task


def restore_task(task_id: int) -> tuple[Task, list[dict]]:
    """Khôi phục với đầy đủ thông tin; báo khi danh sách cũ đã bị xoá (FR-031)."""
    from app.services import auto_deadlines  # tránh import vòng

    task = _trashed(task_id)
    warnings = []
    if task.trashed_from_list_name is not None:
        warnings.append(
            {
                "code": "list_replaced",
                "message": f"Danh sách cũ “{task.trashed_from_list_name}” đã bị xoá, công việc "
                f"được đưa về {task.list.name}",
            }
        )
    task.deleted_at = None
    task.trashed_from_list_name = None
    session = _set_auto_suppressed(task, False)
    if session is not None:
        auto_deadlines.reconcile(session_ids=[session.id])
    bump_revision(db.session)
    db.session.commit()
    return task, warnings


def delete_permanently(task_id: int) -> None:
    task = get_task(task_id, include_trashed=True)
    if task.deleted_at is None:
        raise ApiError(409, "conflict", "Chỉ xoá vĩnh viễn được công việc đang ở Thùng rác")
    db.session.delete(task)
    db.session.commit()


def empty_trash() -> int:
    deleted = db.session.execute(delete(Task).where(Task.deleted_at.is_not(None))).rowcount
    db.session.commit()
    return deleted


def purge_expired_trash(now: datetime) -> int:
    """Xoá hẳn task ở Thùng rác quá 30 ngày (research R6). Task này đã không còn trong feed."""
    cutoff = now - timedelta(days=TRASH_KEEP_DAYS)
    deleted = db.session.execute(
        delete(Task).where(Task.deleted_at.is_not(None), Task.deleted_at < cutoff)
    ).rowcount
    if deleted:
        db.session.commit()
    return deleted


_last_purge: dict[str, datetime | None] = {"at": None}


def purge_expired_trash_throttled(now: datetime) -> int:
    """Như `purge_expired_trash` nhưng tối đa 1 lần/giờ cho mỗi tiến trình (gọi từ /sync/feed)."""
    last = _last_purge["at"]
    if last is not None and now - last < PURGE_EVERY:
        return 0
    _last_purge["at"] = now
    return purge_expired_trash(now)


def reset_purge_throttle() -> None:
    """Chỉ dùng trong test."""
    _last_purge["at"] = None
