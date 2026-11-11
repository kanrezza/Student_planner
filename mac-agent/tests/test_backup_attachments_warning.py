"""Cảnh báo file đính kèm lớn sau sao lưu tự động: tối đa một lần mỗi ngày (feature 005, FR-026)."""

from datetime import datetime
from datetime import time as dtime
from pathlib import Path

from lichhoc_agent.backup import BackupConfig, BackupService
from lichhoc_agent.notify import attachments_notice_body, attachments_notice_due
from lichhoc_agent.state import State

NOW = datetime(2026, 11, 11, 21, 0, 5)


def test_chi_bao_khi_vuot_nguong_va_chua_bao_hom_nay():
    assert attachments_notice_due(True, None, "2026-11-11")
    assert attachments_notice_due(True, "2026-11-10", "2026-11-11")
    assert not attachments_notice_due(True, "2026-11-11", "2026-11-11")
    assert not attachments_notice_due(False, None, "2026-11-11")


def test_noi_dung_thong_bao():
    body = attachments_notice_body(1_288_490_189, 1_395_864_371)
    assert body == "File đính kèm đang chiếm 1,2 GB; mỗi bản sao lưu khoảng 1,3 GB."
    assert "MB" in attachments_notice_body(5 << 20, 6 << 20)


class FakeBackend:
    def __init__(self, warning=True):
        self.warning = warning
        self.status_calls = 0

    def backup_config(self):
        return {
            "enabled": True,
            "schedule_time": "21:00",
            "destination_path": None,
            "retention_count": 14,
            "enabled_since": "2026-11-01T00:00:00",
        }

    def claim_job(self):
        return None

    def backup_status(self):
        self.status_calls += 1
        return {
            "attachments_warning": self.warning,
            "attachments_bytes": 1_288_490_189,
            "estimated_backup_bytes": 1_395_864_371,
        }

    def put_backup_report(self, report):
        pass


def make_service(tmp_path: Path, backend, sent: list[str]):
    state = State(path=tmp_path / "state.json")
    service = BackupService(
        backend,
        state,
        clock=lambda: NOW,
        send_notice=lambda: True,
        send_text=lambda body: sent.append(body) or True,
    )
    service.config = BackupConfig(
        enabled=True,
        schedule_time=dtime(21, 0),
        destination_path=str(tmp_path),
        retention_count=14,
        enabled_since=datetime(2026, 11, 1),
    )
    return service, state


def test_gui_mot_lan_moi_ngay_sau_khi_sao_luu_tu_dong_thanh_cong(tmp_path):
    sent: list[str] = []
    service, state = make_service(tmp_path, FakeBackend(), sent)
    service._maybe_notify_attachments(NOW)
    service._maybe_notify_attachments(NOW)
    assert len(sent) == 1 and state.attachments_notified_on == "2026-11-11"
    assert State.load(state.path).attachments_notified_on == "2026-11-11"
    next_day = datetime(2026, 11, 12, 21, 0)
    service._maybe_notify_attachments(next_day)
    assert len(sent) == 2


def test_khong_gui_khi_chua_vuot_nguong(tmp_path):
    sent: list[str] = []
    service, state = make_service(tmp_path, FakeBackend(warning=False), sent)
    service._maybe_notify_attachments(NOW)
    assert sent == [] and state.attachments_notified_on is None
