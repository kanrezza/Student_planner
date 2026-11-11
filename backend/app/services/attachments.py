"""File đính kèm: dòng CSDL (mục đính kèm, nội dung) và dọn dẹp (feature 005).

Phần đĩa nằm ở `attachments_store`; module này giữ logic có CSDL.
"""

import logging

from sqlalchemy import select

from app.extensions import db
from app.models import AttachmentBlob
from app.services import attachments_store as store

log = logging.getLogger(__name__)


def sweep_orphans() -> int:
    """Dọn file/thư mục tạm lạ trong volume (R6); lỗi chỉ ghi log, không chặn việc khác."""
    try:
        known = set(db.session.scalars(select(AttachmentBlob.sha256)))
        return store.sweep(known)
    except Exception as error:  # noqa: BLE001 — dọn dẹp không được làm hỏng tiến trình chính
        log.warning("Bỏ qua dọn file đính kèm: %s", error)
        return 0
