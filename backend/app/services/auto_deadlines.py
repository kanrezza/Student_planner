"""Tự tạo deadline cho môn đặc biệt (US10, FR-046 đến FR-050, research R9).

Hàm thuần (`eligible`, `due_at`, `title_for`, `plan`) quyết định cần tạo/sửa/xoá task nào;
`reconcile` đọc database, gọi `plan` rồi ghi **trực tiếp** vào model `Task` (không qua
`services.tasks`, vì các hàm đó đánh dấu "người dùng đã sửa").
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.extensions import db
from app.lib import timeutil
from app.lib.text import contains_ci
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, Settings, Subject, Task, TaskList
from app.services.revision import bump_revision

PRIORITY_MEDIUM = 2
E_LEARNING = "e_learning"


# ---- Hàm thuần ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rules:
    evening_from: time
    due_time: time
    excluded: list[str]


@dataclass(frozen=True)
class SessionInfo:
    id: int
    date: date
    start_local: time
    end_at: datetime
    is_cancelled: bool
    subject_name: str
    tag_keys: frozenset[str]  # system_key của các nhãn hiệu lực (môn + buổi)
    suppressed: bool  # người dùng đã xoá task tự tạo của buổi này


@dataclass(frozen=True)
class AutoTaskInfo:
    id: int
    session_id: int
    title: str
    due: datetime
    completed: bool
    user_modified: bool


@dataclass(frozen=True)
class Create:
    session_id: int
    title: str
    due: datetime


@dataclass(frozen=True)
class Update:
    task_id: int
    title: str
    due: datetime


@dataclass(frozen=True)
class Delete:
    task_id: int


def eligible(session: SessionInfo, rules: Rules) -> bool:
    """Buổi chưa huỷ, môn không thuộc ngoại lệ, và (có nhãn E-Learning hoặc bắt đầu từ mốc giờ)."""
    if session.is_cancelled:
        return False
    if any(contains_ci(session.subject_name, keyword) for keyword in rules.excluded):
        return False
    return E_LEARNING in session.tag_keys or session.start_local >= rules.evening_from


def due_at(session_end: datetime, due_time: time) -> datetime:
    """Chủ Nhật đầu tiên lúc `due_time` **sau** khi buổi học kết thúc (giờ Việt Nam)."""
    end = session_end.astimezone(TZ)
    days_to_sunday = (6 - end.weekday()) % 7  # weekday(): Thứ Hai = 0 … Chủ Nhật = 6
    candidate = combine(end.date() + timedelta(days=days_to_sunday), due_time)
    if candidate <= end:
        candidate += timedelta(days=7)
    return candidate


def title_for(subject_name: str, session_date: date) -> str:
    return f"Bài tập {subject_name} – buổi {session_date:%d/%m}"


def plan(
    sessions: list[SessionInfo], tasks: list[AutoTaskInfo], rules: Rules, now: datetime
) -> list[Create | Update | Delete]:
    """Bảng trạng thái research R9; chỉ đụng tới hạn chót chưa qua."""
    by_session = {t.session_id: t for t in tasks}
    actions: list[Create | Update | Delete] = []
    for s in sessions:
        task = by_session.get(s.id)
        wanted = eligible(s, rules)
        due = due_at(s.end_at, rules.due_time)
        title = title_for(s.subject_name, s.date)
        if task is None:
            if wanted and not s.suppressed and due >= now:
                actions.append(Create(session_id=s.id, title=title, due=due))
            continue
        if task.completed or task.user_modified or task.due < now:
            continue  # task thuộc về người dùng, hoặc đã qua hạn
        if not wanted:
            actions.append(Delete(task_id=task.id))
        elif (task.title, task.due) != (title, due):
            actions.append(Update(task_id=task.id, title=title, due=due))
    return actions


# ---- Đọc/ghi database -------------------------------------------------------------------------


def _rules() -> Rules:
    settings = db.session.get(Settings, 1)
    return Rules(
        evening_from=settings.auto_deadline_evening_from,
        due_time=settings.auto_deadline_due_time,
        excluded=list(settings.auto_deadline_excluded_keywords),
    )


def _session_info(s: ClassSession) -> SessionInfo:
    return SessionInfo(
        id=s.id,
        date=s.date,
        start_local=s.start_at.astimezone(TZ).time(),
        end_at=s.end_at,
        is_cancelled=s.is_cancelled,
        subject_name=s.subject.name,
        tag_keys=frozenset(t.system_key for t in s.effective_tags if t.system_key),
        suppressed=s.auto_task_suppressed,
    )


def _task_due(task: Task) -> datetime:
    return combine(task.due_date, task.due_time or time(23, 59))


def _apply(actions: list[Create | Update | Delete], tasks_by_id: dict[int, Task]) -> None:
    study_list = db.session.scalars(select(TaskList).where(TaskList.is_default_study)).one()
    for action in actions:
        if isinstance(action, Create):
            local = action.due.astimezone(TZ)
            db.session.add(
                Task(
                    list_id=study_list.id,
                    title=action.title,
                    due_date=local.date(),
                    due_time=local.time(),
                    priority=PRIORITY_MEDIUM,
                    is_auto=True,
                    source_session_id=action.session_id,
                )
            )
        elif isinstance(action, Update):
            task, local = tasks_by_id[action.task_id], action.due.astimezone(TZ)
            task.title, task.due_date, task.due_time = action.title, local.date(), local.time()
        else:
            db.session.delete(tasks_by_id[action.task_id])


def reconcile(
    session_ids: list[int] | None = None,
    subject_ids: list[int] | None = None,
    all_future: bool = False,
) -> None:
    """Đưa task tự tạo về khớp quy tắc cho các buổi được chỉ định (trong transaction hiện tại)."""
    db.session.flush()
    db.session.expire_all()  # đọc lại nhãn/giờ vừa ghi trong transaction này
    query = select(ClassSession)
    if all_future:
        query = query.where(ClassSession.date >= timeutil.today() - timedelta(days=7))
    elif session_ids or subject_ids:
        if session_ids:
            query = query.where(ClassSession.id.in_(session_ids))
        if subject_ids:
            query = query.where(ClassSession.subject_id.in_(subject_ids))
    else:
        return
    sessions = list(db.session.scalars(query))
    if not sessions:
        return
    tasks = db.session.scalars(
        select(Task).where(Task.is_auto, Task.source_session_id.in_([s.id for s in sessions]))
    ).all()
    infos = [
        AutoTaskInfo(
            id=t.id,
            session_id=t.source_session_id,
            title=t.title,
            due=_task_due(t),
            completed=t.completed_at is not None,
            user_modified=t.user_modified,
        )
        for t in tasks
    ]
    actions = plan([_session_info(s) for s in sessions], infos, _rules(), timeutil.now())
    if actions:
        _apply(actions, {t.id: t for t in tasks})
        bump_revision(db.session)


def drop_for_sessions(session_ids: list[int]) -> None:
    """Gọi TRƯỚC khi xoá buổi học: xoá task tự tạo chưa hoàn thành, chưa bị sửa (FR-049).

    Task đã hoàn thành hoặc đã sửa được giữ lại (liên kết tới buổi học tự về NULL).
    """
    if not session_ids:
        return
    for task in db.session.scalars(
        select(Task).where(
            Task.is_auto,
            Task.source_session_id.in_(session_ids),
            Task.completed_at.is_(None),
            Task.user_modified.is_(False),
        )
    ):
        db.session.delete(task)


def drop_for_subjects(subject_ids: list[int]) -> None:
    ids = db.session.scalars(
        select(ClassSession.id).where(ClassSession.subject_id.in_(subject_ids))
    ).all()
    drop_for_sessions(list(ids))


def subject_ids_of_semester(semester_id: int) -> list[int]:
    return list(db.session.scalars(select(Subject.id).where(Subject.semester_id == semester_id)))
