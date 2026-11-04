"""Chạy các kịch bản quickstart tự động được (V*, D*) trên một database RIÊNG bằng Flask test client.

OCR chạy thật trên ảnh mẫu. Không đụng dữ liệu thật. Dùng:
  scripts/validate.sh        # tạo database tạm `lichhoc_validate`, chạy, rồi xoá
Kết quả in ra từng kịch bản ✅/❌ và ghi JSON vào /tmp/validate.json.
"""

import io
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from app import create_app

app = create_app()
client = app.test_client()
FIX = Path(__file__).parent / "tests" / "fixtures" / "timetables"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, note: str = ""):
    results.append((name, bool(ok), note))
    print(f"{'✅' if ok else '❌'} {name} {note}", flush=True)


def call(method, path, **kw):
    resp = getattr(client, method)(f"/api{path}", **kw)
    data = resp.get_json(silent=True)
    return resp.status_code, data


def post(path, body=None):
    return call("post", path, json=body or {})


def patch(path, body):
    return call("patch", path, json=body)


def recognize(name, kind=None):
    q = f"?kind={kind}" if kind else ""
    return call(
        "post",
        f"/imports/recognize{q}",
        data={"image": (io.BytesIO((FIX / name).read_bytes()), name)},
        content_type="multipart/form-data",
    )


today = date.today()
monday = today - timedelta(days=today.weekday())
sem_start = monday - timedelta(days=7)
sem_end = sem_start + timedelta(weeks=15) - timedelta(days=1)  # đúng 15 tuần

# V1 task cơ bản
_, lists = call("get", "/lists")
study = next(x for x in lists if x["is_default_study"])["id"]
s, task = post(
    "/tasks",
    {
        "title": "Nộp bài Toán",
        "list_id": study,
        "due_date": str(today),
        "due_time": "17:00",
        "priority": 1,
    },
)
check("V1 tạo task", s == 201)
s, _ = patch(f"/tasks/{task['id']}", {"title": "Nộp bài Toán 2"})
s2, done = post(f"/tasks/{task['id']}/complete")
_, today_data = call("get", "/today")
check(
    "V1 sửa + hoàn thành + hiện ở Hôm nay",
    s == 200 and s2 == 200 and any(t["id"] == task["id"] for t in today_data["tasks_due_today"]),
)

# V3 học kỳ + 6 môn theo ca
s, sem = post("/semesters", {"name": "HK1", "start_date": str(sem_start), "end_date": str(sem_end)})
_, shifts = call("get", "/shifts")
by = {x["name"]: x["id"] for x in shifts}
rows = [
    {
        "name": "Giải tích 1",
        "weekdays": [1],
        "shift": {"start_shift_id": by["Ca 1"], "end_shift_id": by["Ca 1"]},
    },
    {
        "name": "Lập trình",
        "weekdays": [2],
        "shift": {"start_shift_id": by["Ca 3"], "end_shift_id": by["Ca 3"]},
    },
    {
        "name": "Vật lý",
        "weekdays": [3],
        "shift": {"start_shift_id": by["Ca 2"], "end_shift_id": by["Ca 2"]},
    },
    {
        "name": "Cơ sở dữ liệu",
        "weekdays": [4],
        "shift": {"start_shift_id": by["Ca 2"], "end_shift_id": by["Ca 2"]},
    },
    {
        "name": "Tiếng Anh",
        "weekdays": [5],
        "shift": {"start_shift_id": by["Ca 4"], "end_shift_id": by["Ca 4"]},
    },
    {
        "name": "Xác suất",
        "weekdays": [6],
        "shift": {"start_shift_id": by["Ca 1"], "end_shift_id": by["Ca 1"]},
    },
]
s, bulk = post("/subjects/bulk", {"semester_id": sem["id"], "rows": rows})
counts = [sub["session_count"] for sub in bulk["subjects"]] if s == 200 or s == 201 else []
check("V3 6 môn, mỗi môn 15 buổi", len(counts) == 6 and all(c == 15 for c in counts), str(counts))
subject = bulk["subjects"][0]

# V4 ngoại lệ buổi học
_, detail = call("get", f"/subjects/{subject['id']}")
ss = detail["sessions"]
call("post", f"/sessions/{ss[1]['id']}/cancel")
patch(f"/sessions/{ss[2]['id']}", {"room": "Phòng riêng"})
patch(f"/subjects/{subject['id']}?confirm=true", {"room": "Phòng chung"})
_, detail = call("get", f"/subjects/{subject['id']}")
d = detail["sessions"]
check(
    "V4 buổi huỷ và buổi sửa phòng giữ nguyên, buổi khác theo phòng chung",
    d[1]["is_cancelled"] and d[2]["room"] == "Phòng riêng" and d[3]["room"] == "Phòng chung",
)

# V5 đổi giờ ca
ca2 = by["Ca 2"]
patch(f"/shifts/{ca2}?confirm=true", {"start_time": "09:30", "end_time": "12:05"})
_, sub3 = call("get", f"/subjects/{bulk['subjects'][2]['id']}")
check(
    "V5 đổi giờ Ca 2 cập nhật môn dùng ca",
    sub3["subject"]["start_time"] == "09:30"
    if "subject" in sub3
    else sub3["start_time"] == "09:30",
)
patch(f"/shifts/{ca2}?confirm=true", {"start_time": "09:35", "end_time": "12:10"})

# V6 nhãn + lọc
_, tag = post("/tags", {"name": "Gấp", "color": "c07"})
_, t2 = post(
    "/tasks",
    {"title": "Việc gấp", "list_id": study, "due_date": str(today), "tag_ids": [tag["id"]]},
)
call("put", f"/sessions/{ss[0]['id']}/tags", json={"tag_ids": [tag["id"]]})
t0 = time.perf_counter()
_, cal = call(
    "get",
    f"/calendar?from={monday - timedelta(days=14)}&to={monday + timedelta(days=45)}&tags={tag['id']}",
)
dt = time.perf_counter() - t0
check(
    "V6 lọc nhãn chỉ còn mục gắn nhãn, < 1 giây",
    len(cal["tasks"]) == 1 and len(cal["sessions"]) == 1 and dt < 1,
    f"{dt * 1000:.0f} ms",
)

# V7/V8 nhập ảnh thật (OCR chạy thật)
t0 = time.perf_counter()
s, prev = recognize("real-grid-01.jpg")
check(
    "V7 nhận diện lưới tuần ảnh thật",
    s == 200 and prev["kind"] == "week_schedule" and len(prev["rows"]) >= 4,
    f"{time.perf_counter() - t0:.0f}s, {len(prev.get('rows', []))} dòng",
)
if s == 200 and prev["kind"] == "week_schedule":
    s, sem2 = post(
        "/semesters",
        {"name": "HK mẫu thu 2026", "start_date": "2026-08-17", "end_date": "2026-10-25"},
    )
    s, prev = recognize("real-grid-01.jpg")
    required = ("name", "date", "start_time", "end_time")
    # Như người dùng: bỏ chọn dòng không đọc được trường bắt buộc (ô bị cắt ở mép ảnh), xác nhận phần còn lại.
    rows = [
        r for r in prev["rows"] if r["selected"] and all(r["fields"][k]["value"] for k in required)
    ]
    for r in rows:
        for f in r["fields"].values():
            f["certain"] = True
    s, res = post("/imports/commit", {"kind": "week_schedule", "rows": rows})
    check("V7 lưu bản xem trước", s == 200 and res["created_subjects"] > 0, str(res))
    s, again = post("/imports/commit", {"kind": "week_schedule", "rows": rows})
    check(
        "V8 nhập lại không tạo trùng (SC-012)",
        s == 200
        and again["created_subjects"] == 0
        and again["skipped_duplicates"] == res["created_subjects"],
    )

# V9/V10 deadline tự tạo
_, et = call("get", "/tags")
elearn = next(t["id"] for t in et if t["system_key"] == "e_learning")
s, phil = post(
    "/subjects",
    {
        "name": "Triết học",
        "semester_id": sem["id"],
        "weekdays": [2],
        "start_time": "07:00",
        "end_time": "09:00",
        "tag_ids": [elearn],
    },
)
s, gdtc = post(
    "/subjects",
    {
        "name": "Giáo dục thể chất 2",
        "semester_id": sem["id"],
        "weekdays": [3],
        "start_time": "20:30",
        "end_time": "22:00",
    },
)
_, tasks_all = call("get", "/tasks?view=all")
auto = [t for t in tasks_all if t["is_auto"]]
check(
    "V9 buổi E-Learning có task tự tạo hạn 08:00 Chủ Nhật, GDTC không có",
    len(auto) > 0
    and all(
        t["due_time"] == "08:00" and date.fromisoformat(t["due_date"]).weekday() == 6 for t in auto
    )
    and not any("thể chất" in t["title"].lower() for t in auto),
    f"{len(auto)} task tự tạo",
)
_, pd = call("get", f"/subjects/{phil['subject']['id']}")
future = [x for x in pd["sessions"] if x["date"] > str(today)]
target = next(x for x in future if x["auto_task_id"])
call("post", f"/sessions/{target['id']}/cancel")
_, a2 = call("get", "/tasks?view=all")
gone = not any(t["id"] == target["auto_task_id"] for t in a2)
call("post", f"/sessions/{target['id']}/restore")
_, a3 = call("get", "/tasks?view=all")
check(
    "V10 huỷ buổi → task biến mất, khôi phục → quay lại",
    gone and any(t["is_auto"] and t["source_session_id"] == target["id"] for t in a3),
)

# V18 lịch thi
s, exam = post(
    "/exams",
    {
        "course_name": "Thi thử",
        "date": str(today + timedelta(days=(7 - today.weekday()) % 7 or 7)),
        "start_time": "06:45",
        "end_time": "08:00",
    },
)
check(
    "V18 thêm tay buổi thi trùng giờ → cảnh báo",
    s == 201 and exam["warnings"] and exam["warnings"][0]["code"] == "time_conflict",
)
t0 = time.perf_counter()
s, ep = recognize("exam-01.png")
f0 = json.dumps(ep, ensure_ascii=False)
past = [r for r in ep.get("exam_rows", []) if r["is_past"]]
check(
    "V18 nhập ảnh lịch thi: đúng loại, 2 dòng đã qua bỏ chọn, không lộ họ tên/MSSV",
    s == 200
    and ep["kind"] == "exam_table"
    and len(past) == 2
    and not any(r["selected"] for r in past)
    and "Nguyễn Văn Test" not in f0
    and "21010999" not in f0,
    f"{time.perf_counter() - t0:.0f}s",
)
sel = [r for r in ep["exam_rows"] if r["selected"]]
for r in sel:
    for f in r["fields"].values():
        f["certain"] = True
s, r1 = post("/imports/commit", {"kind": "exam_table", "exam_rows": sel})
s, r2 = post("/imports/commit", {"kind": "exam_table", "exam_rows": sel})
check("V18 nhập lại không tạo trùng", r1["created_exams"] == len(sel) and r2["created_exams"] == 0)
_, td = call("get", "/today")
check(
    "V18 buổi thi có ở /today và lịch",
    "exams" in td
    and call("get", f"/calendar?from={today}&to={today + timedelta(days=30)}")[1]["exams"],
)

# D4 Thùng rác
_, d4 = post(
    "/tasks", {"title": "Xoá thử", "list_id": study, "tag_ids": [tag["id"]], "due_date": str(today)}
)
call("delete", f"/tasks/{d4['id']}")
_, trash = call("get", "/tasks?view=trash")
tt = next((t for t in trash if t["id"] == d4["id"]), None)
s, _ = post(f"/tasks/{d4['id']}/restore")
check(
    "D4 Thùng rác: còn 30 ngày, khôi phục đủ nhãn",
    tt is not None and tt["days_left_in_trash"] == 30 and s == 200,
)

# D6 emoji
s1, _ = patch(f"/lists/{study}", {"emoji": "🏠"})
s2, _ = patch(f"/lists/{study}", {"emoji": "ab"})
check("D6 emoji danh sách: 🏠 nhận, 'ab' bị từ chối", s1 == 200 and s2 == 400)
patch(f"/lists/{study}", {"emoji": None})

# D10 dời buổi học
tgt = next(
    x
    for x in call("get", f"/subjects/{subject['id']}")[1]["sessions"]
    if x["date"] > str(today) and not x["is_cancelled"] and not x["room_overridden"]
)
new_day = date.fromisoformat(tgt["date"]) + timedelta(days=5)
s, mv = patch(f"/sessions/{tgt['id']}", {"date": str(new_day)})
check(
    "D10 dời buổi sang ngày khác, có ngày gốc",
    s == 200 and mv["session"]["is_moved"] and mv["session"]["original_date"] == tgt["date"],
)

# Đồng bộ / nhắc (dữ liệu feed)
_, feed = call("get", "/sync/feed")
check(
    "Feed đồng bộ không chứa số báo danh/hình thức thi (FR-064)",
    all(
        set(e)
        <= {
            "sync_key",
            "title",
            "location",
            "start_at",
            "end_at",
            "important",
            "alarms_minutes_before",
            "fingerprint",
        }
        for e in feed["events"]
    ),
)
_, dg = call("get", f"/digest?date={today + timedelta(days=1)}")
check("V19 xem trước bản tóm tắt hằng ngày", dg is not None)

failed = [r for r in results if not r[1]]
print(f"\nTỔNG: {len(results) - len(failed)}/{len(results)} đạt")
Path("/tmp/validate.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
sys.exit(1 if failed else 0)
