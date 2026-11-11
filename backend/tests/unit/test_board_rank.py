"""Hàm thuần trạng thái và thứ tự trên bảng Kanban (feature 005)."""

from datetime import datetime

import pytest

from app.lib.timeutil import TZ
from app.services.board_rank import (
    done_window_start,
    needs_rebalance,
    rank_between,
    rebalance,
    task_status,
)

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=TZ)


def test_trang_thai():
    assert task_status(None, False) == "todo"
    assert task_status(None, True) == "doing"
    assert task_status(NOW, False) == "done"
    assert task_status(NOW, True) == "done"  # đã xong thì không còn "đang làm"


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [(None, None, 0.0), (3.0, None, 4.0), (None, 3.0, 2.0), (1.0, 2.0, 1.5), (1.0, 1.0, 1.0)],
)
def test_rank_between(before, after, expected):
    assert rank_between(before, after) == expected


def test_can_sap_lai_khi_qua_sat():
    assert not needs_rebalance([1.0, 2.0, 3.0])
    assert needs_rebalance([1.0, 1.0 + 1e-9])
    assert needs_rebalance([5.0, 5.0])
    assert not needs_rebalance([])
    assert rebalance([9.0, 9.0000001, 12.0]) == [1.0, 2.0, 3.0]


def test_chia_doi_nhieu_lan_roi_sap_lai():
    low, high = 1.0, 2.0
    for _ in range(40):
        high = rank_between(low, high)
    assert needs_rebalance([low, high])


def test_moc_cot_xong_7_ngay():
    assert done_window_start(NOW) == datetime(2026, 11, 5, tzinfo=TZ)
    # Sát nửa đêm giờ Việt Nam vẫn tính theo ngày Việt Nam.
    late = datetime(2026, 11, 11, 23, 59, tzinfo=TZ)
    assert done_window_start(late) == datetime(2026, 11, 5, tzinfo=TZ)
    early = datetime(2026, 11, 12, 0, 1, tzinfo=TZ)
    assert done_window_start(early) == datetime(2026, 11, 6, tzinfo=TZ)
