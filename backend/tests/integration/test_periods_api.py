"""API bảng tiết (feature 004, FR-011…FR-015)."""

from tests.integration.helpers import create_semester  # noqa: F401  (đảm bảo helper import được)


def get_periods(client):
    response = client.get("/api/periods")
    assert response.status_code == 200
    return {p["number"]: p for p in response.get_json()}


def test_danh_sach_mac_dinh(client):
    periods = get_periods(client)
    assert list(periods) == sorted(periods)
    assert {1, 2, 3, 4, 12, 16, 17, 18} <= set(periods)
    assert (periods[1]["start_time"], periods[1]["end_time"]) == ("06:45", "07:35")
    assert (periods[16]["start_time"], periods[16]["end_time"]) == ("21:05", "21:20")
    assert periods[4]["shift_id"] is not None and periods[16]["shift_id"] is None
    assert not any(p["is_manual"] for p in periods.values())


def test_put_tao_va_sua_dat_is_manual(client):
    r = client.put("/api/periods/2", json={"start_time": "07:30", "end_time": "08:20"})
    assert r.status_code == 200 and r.get_json()["is_manual"] is True
    assert get_periods(client)[2]["start_time"] == "07:30"
    r = client.put("/api/periods/13", json={"start_time": "18:00", "end_time": "18:50"})
    assert r.status_code == 200
    assert get_periods(client)[13]["is_manual"] is True


def test_put_loi_va_canh_bao(client):
    r = client.put("/api/periods/13", json={"start_time": "19:00", "end_time": "18:00"})
    assert r.status_code == 400 and "end_time" in r.get_json()["error"]["fields"]
    for number in (0, 31):
        r = client.put(f"/api/periods/{number}", json={"start_time": "18:00", "end_time": "18:50"})
        assert r.status_code == 400
    r = client.put("/api/periods/2", json={"start_time": "07:00", "end_time": "08:00"})
    assert r.status_code == 200
    assert any(w["code"] == "period_overlap" for w in r.get_json()["warnings"])


def test_reset(client):
    client.put("/api/periods/2", json={"start_time": "07:30", "end_time": "08:20"})
    r = client.post("/api/periods/2/reset")
    assert r.status_code == 200
    assert (r.get_json()["start_time"], r.get_json()["is_manual"]) == ("07:40", False)
    client.put("/api/periods/17", json={"start_time": "20:00", "end_time": "20:30"})
    r = client.post("/api/periods/17/reset")
    assert r.get_json()["start_time"] == "21:20"
    client.put("/api/periods/13", json={"start_time": "18:00", "end_time": "18:50"})
    assert client.post("/api/periods/13/reset").status_code == 204
    assert 13 not in get_periods(client)


def test_delete_chi_cho_tiet_khong_thuoc_ca(client):
    assert client.delete("/api/periods/2").status_code == 400
    client.put("/api/periods/13", json={"start_time": "18:00", "end_time": "18:50"})
    assert client.delete("/api/periods/13").status_code == 204
    assert client.delete("/api/periods/13").status_code == 404


def test_doi_gio_ca_tinh_lai_tiet_chua_sua_tay(client):
    shifts = client.get("/api/shifts").get_json()
    ca1 = shifts[0]
    client.put("/api/periods/2", json={"start_time": "07:31", "end_time": "08:21"})  # sửa tay
    r = client.patch(
        f"/api/shifts/{ca1['id']}?confirm=true", json={"start_time": "07:00", "end_time": "09:40"}
    )
    assert r.status_code == 200
    periods = get_periods(client)
    assert (periods[1]["start_time"], periods[1]["end_time"]) == ("07:00", "07:50")
    assert periods[2]["start_time"] == "07:31"  # giữ tiết sửa tay
    assert periods[3]["end_time"] == "09:40"
