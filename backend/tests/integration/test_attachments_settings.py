"""Cài đặt file đính kèm: giới hạn mỗi file, ngưỡng cảnh báo, thống kê (feature 005, US7)."""

import io

import pytest

from tests.integration.test_attachments_api import one, owners, upload  # noqa: F401
from tests.ocr_helpers import load_attachment


def patch(client, **fields):
    return client.patch("/api/settings", json=fields)


def test_gia_tri_mac_dinh(client):
    body = client.get("/api/settings").get_json()
    assert (body["attachment_max_mb"], body["backup_attachments_warn_mb"]) == (50, 1024)


@pytest.mark.parametrize(
    ("field", "value"),
    [("attachment_max_mb", 0), ("attachment_max_mb", 501), ("backup_attachments_warn_mb", 99)],
)
def test_ngoai_khoang_bi_tu_choi_theo_truong(client, field, value):
    response = patch(client, **{field: value})
    assert response.status_code == 400
    assert field in response.get_json()["error"]["fields"]


def test_doi_gioi_han_ap_dung_cho_file_sau_va_giu_file_cu(client, owners):  # noqa: F811
    old = one(client, "task", owners["task"], "de-cuong.pdf")
    assert patch(client, attachment_max_mb=1).status_code == 200
    assert patch(client, attachment_max_mb=10).get_json()["attachment_max_mb"] == 10
    big = upload(client, "task", owners["task"], ("lon.bin", b"x" * (11 * 1024 * 1024)))
    assert big.status_code == 413 and "10 MB" in big.get_json()["errors"][0]["message"]
    still = client.get(f"/api/attachments/{old['id']}")
    assert still.status_code == 200  # file đã gắn không bị ảnh hưởng
    assert io.BytesIO(load_attachment("de-cuong.pdf"))


def test_thong_ke_gop_ban_trung_va_10_file_lon_nhat(client, owners):  # noqa: F811
    data = load_attachment("de-cuong.pdf")
    for i in range(12):
        upload(client, "subject", owners["subject"], (f"f{i}.bin", b"x" * (100 + i)))
    upload(client, "task", owners["task"], ("a.pdf", data))
    upload(client, "exam", owners["exam"], ("b.pdf", data))  # trùng nội dung
    stats = client.get("/api/attachments/stats").get_json()
    assert stats["blob_count"] == 13 and stats["attachment_count"] == 14
    assert stats["total_bytes"] == sum(100 + i for i in range(12)) + len(data)
    assert len(stats["largest"]) == 10
    sizes = [a["size"] for a in stats["largest"]]
    assert sizes == sorted(sizes, reverse=True) and stats["largest"][0]["size"] == len(data)
    assert {"type", "id", "title"} <= set(stats["largest"][0]["owner"])
    assert (stats["max_file_mb"], stats["backup_warn_mb"]) == (50, 1024)
