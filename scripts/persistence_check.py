"""Phần gọi API của scripts/test-persistence.sh (constitution Nguyên tắc V, FR-024, SC-008).

  python3 scripts/persistence_check.py setup  <snapshot.json>   # tạo dữ liệu, lưu ảnh chụp
  python3 scripts/persistence_check.py verify <snapshot.json>   # đọc lại, so với ảnh chụp
  python3 scripts/persistence_check.py add-task <snapshot.json> # tạo thêm task (trước khi kill)
  python3 scripts/persistence_check.py cleanup                  # xoá mọi dữ liệu test

Dữ liệu test có tiền tố "__persist_test__" và học kỳ ở năm 2099 để không đụng dữ liệu thật.
Chỉ dùng thư viện chuẩn của Python.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request

API = "http://127.0.0.1:8080/api"
PREFIX = "__persist_test__"


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{API}{path}", data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} → HTTP {e.code}: {e.read().decode()}") from None


def sql(statement: str) -> None:
    """Đặt trạng thái buổi học trực tiếp (API huỷ/đổi phòng một buổi thuộc User Story 4)."""
    subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "lichhoc",
            "-d",
            "lichhoc",
            "-v",
            "ON_ERROR_STOP=1",
            "-q",
            "-c",
            statement,
        ],
        check=True,
    )


def setup(snapshot_path: str) -> None:
    task_list = call("POST", "/lists", {"name": f"{PREFIX} Danh sách"})
    task = call(
        "POST",
        "/tasks",
        {
            "title": f"{PREFIX} Ôn tập chương 3 “Đạo hàm” – bài 1→5",
            "notes": "Ghi chú có dấu: ắ ằ ẳ ẵ ặ, ơ ư đ",
            "due_date": "2099-02-02",
            "due_time": "17:30",
            "priority": 1,
            "list_id": task_list["id"],
        },
    )
    semester = call(
        "POST",
        "/semesters",
        {
            "name": f"{PREFIX} Học kỳ",
            "start_date": "2099-01-05",
            "end_date": "2099-03-29",
        },
    )
    created = call(
        "POST",
        "/subjects",
        {
            "name": f"{PREFIX} Giải tích 1",
            "semester_id": semester["id"],
            "room": "A2-301",
            "lecturer": "ThS. Nguyễn Văn An",
            "weekdays": [1],
            "start_time": "06:45",
            "end_time": "09:25",
        },
    )
    subject_id = created["subject"]["id"]
    sessions = call("GET", f"/subjects/{subject_id}")["sessions"]
    sql(f"UPDATE class_sessions SET is_cancelled = true WHERE id = {sessions[1]['id']}")
    sql(
        "UPDATE class_sessions SET room = 'Phòng thay đổi', room_overridden = true "
        f"WHERE id = {sessions[2]['id']}"
    )
    snapshot = {
        "list": task_list,
        "task": task,
        "semester": semester,
        "subject": call("GET", f"/subjects/{subject_id}"),
        "extra_task": None,
    }
    write(snapshot_path, snapshot)
    print(
        f"Đã tạo: 1 danh sách, 1 task, 1 học kỳ, 1 môn ({len(sessions)} buổi; 1 huỷ, 1 đổi phòng)"
    )


def add_task(snapshot_path: str) -> None:
    snapshot = read(snapshot_path)
    snapshot["extra_task"] = call(
        "POST",
        "/tasks",
        {
            "title": f"{PREFIX} Ghi ngay trước khi tắt đột ngột",
            "list_id": snapshot["list"]["id"],
        },
    )
    write(snapshot_path, snapshot)


def verify(snapshot_path: str) -> None:
    snapshot = read(snapshot_path)
    checks = {
        "task": (snapshot["task"], call("GET", f"/tasks/{snapshot['task']['id']}")),
        "subject + buổi học": (
            snapshot["subject"],
            call("GET", f"/subjects/{snapshot['subject']['id']}"),
        ),
    }
    lists = {item["id"]: item for item in call("GET", "/lists")}
    checks["danh sách"] = (
        snapshot["list"]["name"],
        lists.get(snapshot["list"]["id"], {}).get("name"),
    )
    semesters = {s["id"]: s for s in call("GET", "/semesters")}
    saved_sem = dict(snapshot["semester"])
    got_sem = dict(semesters.get(saved_sem["id"], {}))
    saved_sem.pop("is_current", None)
    got_sem.pop("is_current", None)
    checks["học kỳ"] = (saved_sem, got_sem)
    if snapshot["extra_task"]:
        extra = snapshot["extra_task"]
        checks["task ghi ngay trước khi tắt đột ngột"] = (
            extra,
            call("GET", f"/tasks/{extra['id']}"),
        )

    failed = False
    for name, (expected, actual) in checks.items():
        if name == "task" or name.startswith("task ghi"):
            expected, actual = without(expected, "is_overdue"), without(actual, "is_overdue")
        if expected != actual:
            failed = True
            print(f"❌ {name} khác sau khi khởi động lại:\n  trước: {expected}\n  sau:   {actual}")
        else:
            print(f"✅ {name} còn nguyên")
    sessions = snapshot["subject"]["sessions"]
    print(
        f"   ({len(sessions)} buổi học; buổi huỷ: {sessions[1]['is_cancelled']}; "
        f"phòng đã sửa: {sessions[2]['room']})"
    )
    if failed:
        raise SystemExit(1)


def cleanup() -> None:
    for semester in call("GET", "/semesters"):
        if semester["name"].startswith(PREFIX):
            call("DELETE", f"/semesters/{semester['id']}?confirm=true")
    for task_list in call("GET", "/lists"):
        if task_list["name"].startswith(PREFIX):
            call("DELETE", f"/lists/{task_list['id']}?delete_tasks=true")


def without(data: dict, key: str) -> dict:
    return {k: v for k, v in data.items() if k != key}


def read(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    command, *args = sys.argv[1:]
    {"setup": setup, "verify": verify, "add-task": add_task, "cleanup": cleanup}[command](*args)
