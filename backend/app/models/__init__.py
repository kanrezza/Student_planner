"""Import mọi model để SQLAlchemy và Alembic (Flask-Migrate) nhìn thấy đầy đủ.

Quan hệ ORM chính (khai báo trong từng file model):
- Semester.subjects, Subject.semester, Subject.schedules (quy tắc lặp), ClassSession.schedule
- Subject.sessions (theo start_at), Subject.tags (theo position)
- ClassSession.subject, ClassSession.tags / effective_tags, ClassSession.auto_task
- Exam.tag_links / Exam.tags (theo position)
- Task.list, Task.source_session, Task.tags (theo position)
"""

from app.models.attachment import Attachment, AttachmentBlob
from app.models.backup import BackupConfig, BackupJob, BackupStatus
from app.models.canonical_name import CanonicalSubjectName
from app.models.class_session import ClassSession
from app.models.exam import Exam
from app.models.period import Period
from app.models.semester import Semester
from app.models.settings import AgentStatus, Settings, SyncState
from app.models.shift import Shift
from app.models.subject import Subject
from app.models.subject_schedule import SubjectSchedule
from app.models.tag import ExamTag, SessionTag, SubjectTag, Tag, TaskTag
from app.models.task import Task
from app.models.task_list import TaskList
from app.models.task_series import TaskSeries

__all__ = [
    "AgentStatus",
    "Attachment",
    "AttachmentBlob",
    "BackupConfig",
    "BackupJob",
    "BackupStatus",
    "CanonicalSubjectName",
    "ClassSession",
    "Exam",
    "ExamTag",
    "Period",
    "Semester",
    "SessionTag",
    "Settings",
    "Shift",
    "Subject",
    "SubjectSchedule",
    "SubjectTag",
    "SyncState",
    "Tag",
    "Task",
    "TaskList",
    "TaskSeries",
    "TaskTag",
]
