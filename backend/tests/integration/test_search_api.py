"""GET /api/search (feature 003 US5, contracts/rest-api.md)."""

from datetime import datetime

import pytest

from app.lib import timeutil
from app.lib.timeutil import TZ
from tests.integration.helpers import create_semester, create_subject

NOW = datetime(2026, 11, 9, 8, 0, tzinfo=TZ)  # Thứ Hai


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(timeutil, "now", lambda: NOW)


def list_id(client) -> int:
    return next(x["id"] for x in client.get("/api/lists").get_json() if x["is_default_study"])


def add_task(client, title, **fields) -> dict:
    resp = client.post("/api/tasks", json={"title": title, "list_id": list_id(client), **fields})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def search(client, q, **params) -> dict:
    query = "&".join([f"q={q}", *(f"{k}={v}" for k, v in params.items())])
    resp = client.get(f"/api/search?{query}")
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["groups"]


def titles(groups, group="tasks"):
    return [item["title"] for item in groups[group]["items"]]


def test_khong_phan_biet_dau_va_hoa_thuong(client):
    add_task(client, "Nộp bài QTDA")
    add_task(client, "Đồ án cuối kỳ")
    for q in ["nop bai", "NỘP BÀI", "Nop%20Bai", "nộp bài"]:
        assert titles(search(client, q)) == ["Nộp bài QTDA"], q
    assert titles(search(client, "do an")) == ["Đồ án cuối kỳ"]
    assert titles(search(client, "ĐỒ ÁN")) == ["Đồ án cuối kỳ"]


def test_nhieu_tu_phai_chua_du_o_bat_ky_vi_tri(client):
    add_task(client, "Nộp bài QTDA")
    add_task(client, "Nộp báo cáo")
    assert titles(search(client, "nop qtda")) == ["Nộp bài QTDA"]
    assert titles(search(client, "qtda%20nop")) == ["Nộp bài QTDA"]
    assert sorted(titles(search(client, "nop"))) == ["Nộp bài QTDA", "Nộp báo cáo"]
    assert titles(search(client, "nop%20zzz")) == []


def test_khop_ghi_chu_co_snippet_quanh_cho_khop(client):
    note = (
        ("Xem lại slide tuần trước. " * 4) + "Gửi qua email thầy Hùng trước thứ sáu. " + ("x " * 40)
    )
    add_task(client, "Việc A", notes=note)
    item = search(client, "email%20thay")["tasks"]["items"][0]
    assert item["matched_field"] == "notes"
    assert "email thầy" in item["snippet"]
    assert 20 <= len(item["snippet"]) <= 100
    assert item["snippet"].startswith("…") and item["snippet"].endswith("…")


def test_khop_tieu_de_thi_matched_field_la_title_khong_snippet(client):
    add_task(client, "Nộp bài", notes="nộp muộn được")
    item = search(client, "nop")["tasks"]["items"][0]
    assert item["matched_field"] == "title" and item["snippet"] is None


def test_task_thung_rac_khong_bao_gio_co(client):
    task = add_task(client, "Việc đã xoá")
    client.delete(f"/api/tasks/{task['id']}")
    assert titles(search(client, "da%20xoa")) == []
    assert titles(search(client, "da%20xoa", include_done=1)) == []


def test_task_da_hoan_thanh_chi_co_khi_include_done(client):
    task = add_task(client, "Nộp bài tuần 1")
    add_task(client, "Nộp bài tuần 2")
    client.post(f"/api/tasks/{task['id']}/complete")
    assert titles(search(client, "nop%20bai")) == ["Nộp bài tuần 2"]
    both = search(client, "nop%20bai", include_done=1)
    assert sorted(titles(both)) == ["Nộp bài tuần 1", "Nộp bài tuần 2"]
    done = next(i for i in both["tasks"]["items"] if i["title"] == "Nộp bài tuần 1")
    assert done["completed"] is True


def test_thu_tu_cong_viec_sap_toi_truoc_da_qua_sau_khong_han_cuoi(client):
    add_task(client, "Việc không hạn")
    add_task(client, "Việc đã qua xa", due_date="2026-11-01")
    add_task(client, "Việc đã qua gần", due_date="2026-11-08")
    add_task(client, "Việc sắp tới xa", due_date="2026-11-30")
    add_task(client, "Việc sắp tới gần", due_date="2026-11-10")
    assert titles(search(client, "viec")) == [
        "Việc sắp tới gần",
        "Việc sắp tới xa",
        "Việc đã qua gần",
        "Việc đã qua xa",
        "Việc không hạn",
    ]


def test_nhom_danh_sach_va_nhan_co_open_count(client):
    tag = client.post("/api/tags", json={"name": "Gấp"}).get_json()
    client.post("/api/tags", json={"name": "Thi cuối kỳ"})
    done = add_task(client, "Xong rồi", tag_ids=[tag["id"]])
    add_task(client, "Đang làm 1", tag_ids=[tag["id"]])
    add_task(client, "Đang làm 2", tag_ids=[tag["id"]])
    client.post(f"/api/tasks/{done['id']}/complete")
    trashed = add_task(client, "Trong rác", tag_ids=[tag["id"]])
    client.delete(f"/api/tasks/{trashed['id']}")
    client.post("/api/lists", json={"name": "Việc nhà", "emoji": "🏠"})

    groups = search(client, "gap")
    assert [(t["name"], t["open_count"]) for t in groups["tags"]["items"]] == [("Gấp", 2)]
    groups = search(client, "viec%20nha")
    assert groups["lists"]["items"][0]["name"] == "Việc nhà"
    assert groups["lists"]["items"][0]["emoji"] == "🏠"
    assert groups["lists"]["items"][0]["open_count"] == 0
    study = search(client, "hoc%20tap")["lists"]["items"][0]
    assert study["open_count"] == 2  # đã hoàn thành và ở Thùng rác không tính


def test_mon_hoc_buoi_hoc_buoi_thi(client):
    semester = create_semester(client)
    subject = create_subject(
        client,
        semester,
        name="Quản trị dự án",
        class_code="QTDA01",
        lecturer="Thầy Hùng",
        room="B2-101",
        weekdays=[1, 3],
    )
    create_subject(client, semester, name="Giải tích 2", class_code="GT2", weekdays=[2])
    client.post(
        "/api/exams",
        json={
            "course_name": "Quản trị dự án",
            "course_code": "QTDA01",
            "date": "2026-11-20",
            "start_time": "07:30",
            "end_time": "09:00",
            "room": "C3-202",
        },
    )

    for q in ["quan%20tri", "qtda01", "thay%20hung"]:
        groups = search(client, q)
        assert [s["name"] for s in groups["subjects"]["items"]] == ["Quản trị dự án"], q
    assert [s["id"] for s in search(client, "quan%20tri")["subjects"]["items"]] == [subject["id"]]

    sessions = search(client, "qtda01")["sessions"]
    assert sessions["total"] > 0
    starts = [s["start_at"] for s in sessions["items"]]
    upcoming = [s for s in starts if s >= "2026-11-09T08:00:00+07:00"]
    past = [s for s in starts if s < "2026-11-09T08:00:00+07:00"]
    assert starts == upcoming + past  # sắp tới trước
    assert upcoming == sorted(upcoming) and past == sorted(past, reverse=True)
    assert sessions["items"][0]["subject"]["name"] == "Quản trị dự án"

    assert search(client, "b2-101")["sessions"]["total"] == sessions["total"]  # theo phòng
    exams = search(client, "c3-202")["exams"]
    assert [e["course_name"] for e in exams["items"]] == ["Quản trị dự án"]
    assert search(client, "qtda01")["exams"]["total"] == 1  # theo mã học phần


def test_gioi_han_moi_nhom_va_xem_them(client):
    for n in range(25):
        add_task(client, f"Bài tập {n:02d}")
    first = search(client, "bai%20tap")["tasks"]
    assert first["total"] == 25 and len(first["items"]) == 20
    more = search(client, "bai%20tap", group="tasks", limit=200)["tasks"]
    assert more["total"] == 25 and len(more["items"]) == 25


def test_q_rong_hoac_khoang_trang_moi_nhom_rong(client):
    add_task(client, "Có việc")
    for q in ["", "%20%20%20"]:
        groups = search(client, q)
        assert all(g["total"] == 0 and g["items"] == [] for g in groups.values()), q
    assert set(groups) == {"tasks", "lists", "tags", "subjects", "sessions", "exams", "files"}


def test_ky_tu_dac_biet_khong_lam_hong_truy_van(client):
    add_task(client, "Tỉ lệ 100% đạt_chuẩn")
    assert titles(search(client, "100%25")) == ["Tỉ lệ 100% đạt_chuẩn"]
    assert (
        titles(search(client, "t_%25")) == []
    )  # % và _ là ký tự thường, không phải ký tự đại diện
    assert titles(search(client, "dat_chuan")) == ["Tỉ lệ 100% đạt_chuẩn"]


def test_group_khong_hop_le(client):
    assert client.get("/api/search?q=a&group=khac").status_code == 400
