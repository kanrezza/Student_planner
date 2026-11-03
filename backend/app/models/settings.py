"""Các bảng một dòng (CHECK id = 1): cài đặt, revision đồng bộ, trạng thái mac-agent."""

from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    SmallInteger,
    Text,
    Time,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class _SingleRow:
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, server_default=text("1"))


class Settings(_SingleRow, db.Model):
    """Cài đặt nhắc và tự tạo deadline (FR-022, FR-048, FR-051)."""

    __tablename__ = "settings"
    __table_args__ = (CheckConstraint("id = 1", name="ck_settings_single_row"),)

    session_reminder_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("15")
    )
    task_reminder_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("60")
    )
    date_only_task_reminder_time: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'08:00'")
    )
    calendar_sync_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    calendar_sync_prompted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    auto_deadline_evening_from: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'20:00'")
    )
    auto_deadline_due_time: Mapped[time] = mapped_column(
        Time, nullable=False, server_default=text("'08:00'")
    )
    auto_deadline_excluded_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("ARRAY['Giáo dục thể chất']::text[]")
    )


class SyncState(_SingleRow, db.Model):
    """`revision` tăng 1 cùng transaction với mọi thay đổi ảnh hưởng tới feed (research R5)."""

    __tablename__ = "sync_state"
    __table_args__ = (CheckConstraint("id = 1", name="ck_sync_state_single_row"),)

    revision: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class AgentStatus(_SingleRow, db.Model):
    """Trạng thái do mac-agent báo về (contracts/calendar-sync.md §3)."""

    __tablename__ = "agent_status"
    __table_args__ = (CheckConstraint("id = 1", name="ck_agent_status_single_row"),)

    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    permission: Mapped[str] = mapped_column(Text, nullable=False, server_default="unknown")
    icloud_source: Mapped[str] = mapped_column(Text, nullable=False, server_default="unknown")
    last_synced_revision: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    last_error: Mapped[str | None] = mapped_column(Text)
