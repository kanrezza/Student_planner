"""Import mọi model để SQLAlchemy và Alembic (Flask-Migrate) nhìn thấy đầy đủ.

Quan hệ ORM chính (khai báo trong từng file model):
- Semester.subjects, Subject.semester
- Subject.sessions (theo start_at), Subject.tags (theo position)
- ClassSession.subject, ClassSession.tags / effective_tags, ClassSession.auto_task
- Task.list, Task.source_session, Task.tags (theo position)
"""

from app.models.class_session import ClassSession
from app.models.semester import Semester
from app.models.settings import AgentStatus, Settings, SyncState
from app.models.shift import Shift
from app.models.subject import Subject
from app.models.tag import SessionTag, SubjectTag, Tag, TaskTag
from app.models.task import Task
from app.models.task_list import TaskList

__all__ = [
    "AgentStatus",
    "ClassSession",
    "Semester",
    "SessionTag",
    "Settings",
    "Shift",
    "Subject",
    "SubjectTag",
    "SyncState",
    "Tag",
    "Task",
    "TaskList",
    "TaskTag",
]
