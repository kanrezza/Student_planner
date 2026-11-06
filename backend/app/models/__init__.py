"""Import mọi model để SQLAlchemy và Alembic (Flask-Migrate) nhìn thấy đầy đủ.

Quan hệ ORM chính (khai báo trong từng file model):
- Semester.subjects, Subject.semester
- Subject.sessions (theo start_at), Subject.tags (theo position)
- ClassSession.subject, ClassSession.tags / effective_tags, ClassSession.auto_task
- Exam.tag_links / Exam.tags (theo position)
- Task.list, Task.source_session, Task.tags (theo position)
"""

from app.models.backup import BackupConfig, BackupJob, BackupStatus
from app.models.class_session import ClassSession
from app.models.exam import Exam
from app.models.semester import Semester
from app.models.settings import AgentStatus, Settings, SyncState
from app.models.shift import Shift
from app.models.subject import Subject
from app.models.tag import ExamTag, SessionTag, SubjectTag, Tag, TaskTag
from app.models.task import Task
from app.models.task_list import TaskList
from app.models.task_series import TaskSeries

__all__ = [
    "AgentStatus",
    "BackupConfig",
    "BackupJob",
    "BackupStatus",
    "ClassSession",
    "Exam",
    "ExamTag",
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
    "TaskSeries",
    "TaskTag",
]
