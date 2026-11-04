"""Trang "Hôm nay" (FR-019): buổi học hôm nay, task hạn hôm nay, nhóm "Quá hạn".

- Task hạn hôm nay gồm cả task đã xong (hiện gạch ngang) để có thể bỏ đánh dấu.
- Task hạn hôm nay mà đã qua giờ vẫn nằm ở nhóm hôm nay (có cờ `is_overdue`), để không hiện hai lần.
- Nhóm "Quá hạn" = task chưa hoàn thành có hạn chót trước hôm nay.
"""

from sqlalchemy import or_, select

from app.extensions import db
from app.lib import timeutil
from app.models import ClassSession, Task
from app.services.tasks import active_tasks, sort_key


def today_view():
    now = timeutil.now()
    today = now.date()
    sessions = db.session.scalars(
        select(ClassSession).where(ClassSession.date == today).order_by(ClassSession.start_at)
    ).all()
    # Gồm task có khung giờ làm hôm nay dù hạn chót ở ngày khác (feature 002 US6).
    due_today = db.session.scalars(
        active_tasks().where(or_(Task.due_date == today, Task.work_date == today))
    ).all()
    listed_today = {t.id for t in due_today}
    overdue = [
        t
        for t in db.session.scalars(
            active_tasks().where(Task.due_date < today, Task.completed_at.is_(None))
        )
        if t.id not in listed_today
    ]
    # Task đã xong xếp cuối nhóm hôm nay.
    due_today = sorted(due_today, key=lambda t: (t.completed_at is not None, sort_key(t)))
    return now, today, sessions, due_today, sorted(overdue, key=sort_key)
