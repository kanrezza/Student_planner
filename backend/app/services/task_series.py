"""Chuỗi task lặp: tạo/đổi quy tắc, sinh lần kế tiếp, sửa/xoá theo phạm vi, lần dự kiến
(feature 003 US3, research R16–R18). Hàm thuần nằm ở `task_recurrence.py`.

Mô hình "một lần hiện tại": mỗi chuỗi có đúng một task thật chưa xong (unique index một phần);
các lần sau chỉ được suy ra từ quy tắc để hiển thị. Hàm ở đây không commit: service task commit.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, exists, select

from app.api.errors import ApiError
from app.extensions import db
from app.models import Tag, Task, TaskList, TaskSeries, TaskTag
from app.services import task_recurrence as rec
from app.services.tag_links import replace_tag_links

MAX_PROJECTED = 400
TEMPLATE_FIELDS = ("title", "notes", "list_id", "priority", "is_important", "reminder_minutes")


def _invalid(fields: dict[str, str]) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", fields)


# ---- Chuyển đổi quy tắc ---------------------------------------------------------------------


def rule_of(series: TaskSeries) -> rec.Rule:
    return rec.Rule(
        freq=series.freq,
        anchor_date=series.anchor_date,
        interval_days=series.interval_days,
        weekdays=tuple(series.weekdays or ()),
        month_day=series.month_day,
        end_kind=series.end_kind,
        end_date=series.end_date,
        end_count=series.end_count,
    )


def rule_from_input(data: dict, anchor: date) -> rec.Rule:
    """`data` là `RecurrenceIn.model_dump()`: {freq, interval_days, weekdays, month_day, end}."""
    end = data.get("end") or {"kind": "never"}
    rule = rec.Rule(
        freq=data["freq"],
        anchor_date=anchor,
        interval_days=data.get("interval_days") if data["freq"] == "every_n_days" else None,
        weekdays=tuple(sorted(set(data.get("weekdays") or ()))) if data["freq"] == "weekly" else (),
        month_day=data.get("month_day") if data["freq"] == "monthly" else None,
        end_kind=end["kind"],
        end_date=end.get("date") if end["kind"] == "on_date" else None,
        end_count=end.get("count") if end["kind"] == "after_count" else None,
    )
    if errors := rec.validate(rule):
        raise _invalid({f"recurrence.{k}": v for k, v in errors.items()})
    return rule


def _store_rule(series: TaskSeries, rule: rec.Rule) -> None:
    series.freq = rule.freq
    series.interval_days = rule.interval_days
    series.weekdays = list(rule.weekdays) if rule.freq == "weekly" else None
    series.month_day = rule.month_day
    series.anchor_date = rule.anchor_date
    series.end_kind = rule.end_kind
    series.end_date = rule.end_date
    series.end_count = rule.end_count


def rule_dict(series: TaskSeries) -> dict:
    """Dạng API của quy tắc (`RecurrenceRule` trong data-model §4)."""
    end: dict = {"kind": series.end_kind}
    if series.end_kind == "on_date":
        end["date"] = series.end_date.isoformat()
    elif series.end_kind == "after_count":
        end["count"] = series.end_count
    result: dict = {"freq": series.freq, "end": end}
    if series.freq == "every_n_days":
        result["interval_days"] = series.interval_days
    elif series.freq == "weekly":
        result["weekdays"] = sorted(series.weekdays or [])
    elif series.freq == "monthly":
        result["month_day"] = series.month_day
    return result


# ---- Mẫu ------------------------------------------------------------------------------------


def _hhmm(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _parse_hhmm(value: str | None) -> time | None:
    return time.fromisoformat(value) if value else None


def _work_template(task: Task) -> dict | None:
    if task.work_date is None or task.due_date is None:
        return None
    return {
        "start": _hhmm(task.work_start),
        "end": _hhmm(task.work_end),
        "day_offset": (task.work_date - task.due_date).days,
    }


def template_of(task: Task) -> dict:
    return {
        "title": task.title,
        "notes": task.notes,
        "list_id": task.list_id,
        "priority": task.priority,
        "is_important": task.is_important,
        "reminder_minutes": task.reminder_minutes,
        "tag_ids": [t.id for t in task.tags],
        "due_time": _hhmm(task.due_time),
        "work": _work_template(task),
    }


def _update_template(series: TaskSeries, task: Task, changes: dict) -> None:
    template = dict(series.template)
    for field in TEMPLATE_FIELDS:
        if field in changes:
            template[field] = getattr(task, field)
    if "tag_ids" in changes:
        template["tag_ids"] = [t.id for t in task.tags]
    if "due_time" in changes:
        template["due_time"] = _hhmm(task.due_time)
    if any(k in changes for k in ("work_date", "work_start", "work_end")):
        template["work"] = _work_template(task)
    series.template = template  # gán lại cả dict để SQLAlchemy ghi nhận thay đổi JSONB


# ---- Tạo, đổi, bỏ quy tắc -------------------------------------------------------------------


def attach_rule(task: Task, data: dict, today: date) -> TaskSeries:
    """Đặt lặp cho task thường. Chưa có hạn → hạn là ngày khớp quy tắc gần nhất từ hôm nay."""
    if task.is_auto:
        raise _invalid({"recurrence": "Công việc tự tạo từ buổi học không đặt lặp được"})
    if task.completed_at is not None:
        raise _invalid({"recurrence": "Công việc đã hoàn thành không đặt lặp được"})
    rule = rule_from_input(data, task.due_date or today)
    if task.due_date is None:
        first = rec.first_due_on_or_after(rule, today)
        if first is None:
            raise _invalid({"recurrence.end": "Ngày kết thúc phải từ hôm nay trở đi"})
        task.due_date = first
    series = TaskSeries(template=template_of(task), occurrences_created=1)
    _store_rule(series, rule)
    db.session.add(series)
    db.session.flush()
    task.series_id = series.id
    task.occurrence_no = 1
    return series


def change_rule(task: Task, data: dict | None) -> None:
    """Đổi hoặc bỏ quy tắc của cả chuỗi (không hỏi phạm vi). Lần hiện tại giữ nguyên hạn."""
    series = task.series
    if data is None:
        task.series_id = None
        task.occurrence_no = None
        task.spawned_from_task_id = None
        db.session.flush()
        db.session.delete(series)  # task cũ trong chuỗi tự về task thường (ON DELETE SET NULL)
        db.session.flush()
        db.session.expire_all()
        return
    rule = rule_from_input(data, task.due_date)
    _store_rule(series, rule)
    series.stopped_at = None


def prune_orphan_series() -> None:
    """Xoá chuỗi không còn task nào (sau khi xoá vĩnh viễn)."""
    db.session.execute(delete(TaskSeries).where(~exists().where(Task.series_id == TaskSeries.id)))


# ---- Sinh lần kế tiếp -----------------------------------------------------------------------


def _usable_list_id(template: dict, fallback: int) -> int:
    return template["list_id"] if db.session.get(TaskList, template["list_id"]) else fallback


def spawn_next(series: TaskSeries, previous: Task, now: datetime) -> Task | None:
    """Tạo lần kế tiếp từ mẫu, không phải từ lần vừa xong (để "Chỉ lần này" không lan sang sau)."""
    if series.stopped_at is not None:
        return None
    template = series.template
    due_time = _parse_hhmm(template.get("due_time"))
    due = rec.next_due(
        rule_of(series), previous.due_date, now, due_time, series.occurrences_created
    )
    if due is None:
        return None
    work = template.get("work")
    nxt = Task(
        list_id=_usable_list_id(template, previous.list_id),
        title=template["title"],
        notes=template.get("notes"),
        due_date=due,
        due_time=due_time,
        priority=template["priority"],
        is_important=template["is_important"],
        reminder_minutes=template.get("reminder_minutes"),
        series_id=series.id,
        spawned_from_task_id=previous.id,
        user_modified=False,
    )
    if work:
        nxt.work_date = due + timedelta(days=work["day_offset"])
        nxt.work_start = _parse_hhmm(work["start"])
        nxt.work_end = _parse_hhmm(work["end"])
    series.occurrences_created += 1
    nxt.occurrence_no = series.occurrences_created
    db.session.add(nxt)
    db.session.flush()
    existing = set(db.session.scalars(select(Tag.id).where(Tag.id.in_(template["tag_ids"]))))
    replace_tag_links(TaskTag, "task_id", nxt.id, [i for i in template["tag_ids"] if i in existing])
    db.session.expire(nxt, ["tag_links"])
    return nxt


def on_complete(task: Task, now: datetime) -> Task | None:
    """Gọi sau khi đặt `completed_at`; trả lần kế tiếp (hoặc None khi chuỗi kết thúc)."""
    if task.series_id is None:
        return None
    return spawn_next(task.series, task, now)


def on_uncomplete(task: Task) -> int | None:
    """Gọi TRƯỚC khi bỏ `completed_at`. Gỡ lần kế tiếp chưa sửa (FR-019); trả id đã gỡ.

    Nếu chuỗi vẫn còn một lần hiện tại khác (lần kế tiếp đã bị sửa) thì giữ cả hai: task được bỏ
    hoàn thành tách khỏi chuỗi để thành task thường (mỗi chuỗi chỉ được có một lần hiện tại).
    """
    if task.series_id is None:
        return None
    series = task.series
    removed = None
    nxt = db.session.scalar(
        select(Task).where(
            Task.series_id == series.id,
            Task.spawned_from_task_id == task.id,
            Task.deleted_at.is_(None),
            Task.completed_at.is_(None),
            Task.user_modified.is_(False),
        )
    )
    if nxt is not None:
        removed = nxt.id
        db.session.delete(nxt)
        series.occurrences_created = max(1, series.occurrences_created - 1)
        db.session.flush()
    if db.session.scalar(
        select(
            exists().where(
                Task.series_id == series.id,
                Task.id != task.id,
                Task.deleted_at.is_(None),
                Task.completed_at.is_(None),
            )
        )
    ):
        task.series_id = None
        task.occurrence_no = None
        task.spawned_from_task_id = None
    return removed


# ---- Sửa theo phạm vi -----------------------------------------------------------------------


def is_live(task: Task) -> bool:
    """Task đang là lần hiện tại của một chuỗi (cần hỏi phạm vi khi sửa/xoá)."""
    return task.series_id is not None and task.completed_at is None


def apply_scoped_edit(task: Task, changes: dict, scope: str, old_due: date | None) -> None:
    """Sau khi `changes` đã áp lên `task`: đánh dấu đã sửa và (nếu "các lần sau") cập nhật mẫu."""
    task.user_modified = True
    if scope != "following":
        return
    series = task.series
    _update_template(series, task, changes)
    if "due_date" in changes and old_due is not None and task.due_date != old_due:
        _store_rule(series, rec.shift_rule(rule_of(series), old_due, task.due_date))


# ---- Xoá, khôi phục -------------------------------------------------------------------------


def on_trash(task: Task, scope: str, now: datetime) -> Task | None:
    """Gọi khi task đã `deleted_at`. `this`: tạo lần kế tiếp; `following`: dừng chuỗi."""
    if task.series_id is None or task.completed_at is not None:
        return None
    task.trash_scope = scope
    series = task.series
    if scope == "following":
        series.stopped_at = now
        return None
    db.session.flush()  # giải phóng chỗ "lần hiện tại" của chuỗi trước khi tạo lần mới
    return spawn_next(series, task, now)


def on_restore(task: Task) -> None:
    scope, task.trash_scope = task.trash_scope, None
    if task.series_id is None or scope is None:
        return
    if scope == "this":  # FR-025: trở lại thành task thường không lặp
        task.series_id = None
        task.occurrence_no = None
        task.spawned_from_task_id = None
        return
    series = task.series
    series.stopped_at = None
    if db.session.scalar(
        select(
            exists().where(
                Task.series_id == series.id,
                Task.id != task.id,
                Task.deleted_at.is_(None),
                Task.completed_at.is_(None),
            )
        )
    ):
        task.series_id = None  # đã có lần hiện tại khác → không để hai lần hiện tại
        task.occurrence_no = None
        task.spawned_from_task_id = None


# ---- Lần dự kiến (suy ra, không lưu) --------------------------------------------------------


@dataclass(frozen=True)
class Projected:
    series_id: int
    current_task_id: int
    day: date
    at_time: time | None
    title: str
    color: str
    important: bool = False


def projected_occurrences(
    start: date, end: date, today: date, tag_ids: list[int] | None = None
) -> list[Projected]:
    """Lần dự kiến trong [start, end]: các ngày khớp quy tắc sau lần hiện tại, từ hôm nay trở đi,
    trước khi chuỗi kết thúc (FR-022, FR-023). Tối đa `MAX_PROJECTED` mục."""
    from app.services.colors import display_color

    query = (
        select(Task, TaskSeries)
        .join(TaskSeries, Task.series_id == TaskSeries.id)
        .where(
            Task.deleted_at.is_(None),
            Task.completed_at.is_(None),
            Task.due_date.is_not(None),
            TaskSeries.stopped_at.is_(None),
        )
        .order_by(Task.due_date, Task.id)
    )
    if tag_ids:
        query = query.where(Task.id.in_(select(TaskTag.task_id).where(TaskTag.tag_id.in_(tag_ids))))
    result: list[Projected] = []
    for task, series in db.session.execute(query):
        rule = rule_of(series)
        lower = max(start, task.due_date + timedelta(days=1), today)
        remaining = (
            max(0, (rule.end_count or 0) - series.occurrences_created)
            if rule.end_kind == "after_count"
            else None
        )
        if lower > end or remaining == 0:
            continue
        # Lần kế tiếp thật có thể bị đẩy muộn hơn vì "không sớm hơn hôm nay"; đếm số lần còn lại từ
        # lower là đủ chính xác cho hiển thị.
        due_time = _parse_hhmm(series.template.get("due_time"))
        color = display_color([t.color for t in task.tags], task.list.color)
        for day in rec.occurrences(rule, lower, end, limit=remaining):
            result.append(
                Projected(
                    series.id,
                    task.id,
                    day,
                    due_time,
                    series.template["title"],
                    color,
                    series.template["is_important"],
                )
            )
            if len(result) >= MAX_PROJECTED:
                return result
    return result
