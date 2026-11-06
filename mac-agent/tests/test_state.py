from lichhoc_agent.state import State


def test_state_luu_va_doc_lai_khoa_sao_luu(tmp_path):
    path = tmp_path / "state.json"
    state = State(path=path)
    state.backup_last_success_at = "2026-11-05T21:00:12"
    state.backup_last_attempt_ok = True
    state.backup_last_success_size = 2516582
    state.stale_notified_for = "2026-11-01T21:00:00"
    state.save()
    loaded = State.load(path)
    assert loaded.backup_last_success_at == "2026-11-05T21:00:12"
    assert loaded.backup_last_attempt_ok is True
    assert loaded.backup_last_success_size == 2516582
    assert loaded.stale_notified_for == "2026-11-01T21:00:00"


def test_state_cu_khong_co_khoa_sao_luu_van_doc_duoc(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"calendar_id": "abc", "last_revision": 7}', encoding="utf-8")
    loaded = State.load(path)
    assert loaded.calendar_id == "abc" and loaded.last_revision == 7
    assert loaded.backup_last_success_at is None


def test_clear_khong_xoa_trang_thai_sao_luu(tmp_path):
    state = State(path=tmp_path / "state.json")
    state.calendar_id = "abc"
    state.backup_last_success_at = "2026-11-05T21:00:12"
    state.clear()
    assert state.calendar_id is None
    assert state.backup_last_success_at == "2026-11-05T21:00:12"
