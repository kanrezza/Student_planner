"""Đánh dấu có thay đổi cho mac-agent (research R5, data-model "Quy tắc đánh dấu revision")."""

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import SyncState


def bump_revision(session: Session) -> None:
    """Tăng `sync_state.revision` trong transaction hiện tại; gọi từ lớp service khi ghi dữ liệu."""
    session.execute(
        update(SyncState).where(SyncState.id == 1).values(revision=SyncState.revision + 1)
    )


def current_revision(session: Session) -> int:
    return session.get(SyncState, 1).revision
