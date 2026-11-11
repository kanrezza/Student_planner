"""Phần gọi API của scripts/test-persistence.sh (constitution Nguyên tắc V, FR-024, SC-008).

  python3 scripts/persistence_check.py setup  <snapshot.json>   # tạo dữ liệu, lưu ảnh chụp
  python3 scripts/persistence_check.py verify <snapshot.json>   # đọc lại, so với ảnh chụp
  python3 scripts/persistence_check.py add-task <snapshot.json> # tạo thêm task (trước khi kill)
  python3 scripts/persistence_check.py cleanup                  # xoá mọi dữ liệu test
  python3 scripts/persistence_check.py backup-check             # kiểm tra sao lưu

Dữ liệu test có tiền tố "__persist_test__" và học kỳ ở năm 2099 để không đụng dữ liệu thật.
Chỉ dùng thư viện chuẩn của Python.
"""

import hashlib
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


def upload_attachment(owner_type: str, owner_id: int, name: str, content: bytes) -> dict:
    """Gắn file đính kèm bằng multipart (chỉ dùng thư viện chuẩn)."""
    boundary = "----persist" + hashlib.sha256(content).hexdigest()[:16]
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="owner_type"\r\n\r\n'
        f"{owner_type}\r\n",
        f'--{boundary}\r\nContent-Disposition: form-data; name="owner_id"\r\n\r\n{owner_id}\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n",
    ]
    body = "".join(parts).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{API}/attachments",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())["attachments"][0]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"POST /attachments → HTTP {e.code}: {e.read().decode()}") from None


def fetch_bytes(path: str) -> bytes:
    with urllib.request.urlopen(f"http://127.0.0.1:8080{path}", timeout=60) as response:
        return response.read()


ATTACHMENT_NAME = f"{PREFIX} Đề cương.bin"
ATTACHMENT_CONTENT = (PREFIX.encode() + b" noi dung file dinh kem ") * 2000


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
    task_list = call("POST", "/lists", {"name": f"{PREFIX} Danh sách", "emoji": "📚"})
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
    # Task trong Thùng rác (feature 002 FR-030) phải còn ở Thùng rác sau khởi động lại.
    trashed = call(
        "POST",
        "/tasks",
        {
            "title": f"{PREFIX} Đã chuyển vào Thùng rác",
            "list_id": task_list["id"],
            "work_date": "2099-02-01",
            "work_start": "19:00",
            "work_end": "21:00",
        },
    )
    trashed = call("DELETE", f"/tasks/{trashed['id']}")
    # Bảng Kanban (feature 005): task "Đang làm" có thứ tự trên bảng, kèm một file đính kèm.
    doing = call(
        "POST",
        "/tasks",
        {"title": f"{PREFIX} Đang làm", "list_id": task_list["id"], "status": "doing"},
    )
    attachment = upload_attachment("task", doing["id"], ATTACHMENT_NAME, ATTACHMENT_CONTENT)
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
        "trashed": trashed,
        "doing": call("GET", f"/tasks/{doing['id']}"),
        "attachment": {
            "id": attachment["id"],
            "name": attachment["display_name"],
            "size": attachment["size"],
            "sha256": hashlib.sha256(ATTACHMENT_CONTENT).hexdigest(),
        },
        "semester": semester,
        "subject": call("GET", f"/subjects/{subject_id}"),
        "extra_task": None,
    }
    write(snapshot_path, snapshot)
    print(
        "Đã tạo: 1 danh sách, 1 task, 1 task trong Thùng rác, 1 task Đang làm kèm 1 file, "
        f"1 học kỳ, 1 môn ({len(sessions)} buổi; 1 huỷ, 1 đổi phòng)"
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
    saved_list = lists.get(snapshot["list"]["id"], {})
    checks["danh sách (tên, emoji)"] = (
        (snapshot["list"]["name"], snapshot["list"]["emoji"]),
        (saved_list.get("name"), saved_list.get("emoji")),
    )
    trash = {t["id"]: t for t in call("GET", "/tasks?view=trash")}
    kept = ("title", "deleted_at", "work_date", "work_start", "work_end")
    expected_trashed = snapshot["trashed"]
    got_trashed = trash.get(expected_trashed["id"], {})
    checks["task trong Thùng rác"] = (
        {k: expected_trashed[k] for k in kept},
        {k: got_trashed.get(k) for k in kept},
    )
    doing = snapshot["doing"]
    got_doing = call("GET", f"/tasks/{doing['id']}")
    checks["task Đang làm (trạng thái, thứ tự trên bảng)"] = (
        (doing["status"], doing["board_rank"], doing["attachment_count"]),
        (got_doing["status"], got_doing["board_rank"], got_doing["attachment_count"]),
    )
    saved_file = snapshot["attachment"]
    listed = call("GET", f"/attachments?owner_type=task&owner_id={doing['id']}")
    content = fetch_bytes(f"/api/attachments/{saved_file['id']}/download")
    checks["file đính kèm (tên, dung lượng, nội dung SHA-256)"] = (
        (saved_file["name"], saved_file["size"], saved_file["sha256"]),
        (
            listed[0]["display_name"] if listed else None,
            listed[0]["size"] if listed else None,
            hashlib.sha256(content).hexdigest(),
        ),
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
    # Xoá danh sách đưa task vào Thùng rác → xoá hẳn các task test ở đó.
    for task in call("GET", "/tasks?view=trash"):
        if task["title"].startswith(PREFIX):
            call("DELETE", f"/tasks/{task['id']}?permanent=true")


def backup_check() -> None:
    """Sao lưu (feature 003): bản .lhbackup tạo được, đọc lại khớp số liệu hiện tại, và nginx nhận
    được file lớn hơn 21 MB (gửi file rác 30 MB → backend trả 400 "bị hỏng", KHÔNG phải 413).

    Cố ý KHÔNG khôi phục lên database thật; việc khôi phục được test trên database riêng
    (backend/tests/integration/test_restore_api.py).
    """
    import hashlib
    import io
    import zipfile

    with urllib.request.urlopen(f"{API}/backup/dump?kind=thu-cong", timeout=300) as response:
        data = response.read()
        expected_sha = response.headers["X-Backup-Sha256"]
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise SystemExit("Mã SHA-256 của bản sao lưu không khớp header")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        dump = zf.read("data.dump")
    if hashlib.sha256(dump).hexdigest() != manifest["dump_sha256"]:
        raise SystemExit("Dump trong bản sao lưu không khớp manifest")
    counts_now = {"task_lists": len(call("GET", "/lists"))}
    # File đính kèm (feature 005): bản sao lưu format 2 chứa nội dung từng file, tên theo SHA-256.
    expected_blob = hashlib.sha256(ATTACHMENT_CONTENT).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if manifest.get("format") != 2 or f"attachments/{expected_blob}" not in zf.namelist():
            raise SystemExit("Bản sao lưu thiếu file đính kèm của dữ liệu thử")
        if hashlib.sha256(zf.read(f"attachments/{expected_blob}")).hexdigest() != expected_blob:
            raise SystemExit("File đính kèm trong bản sao lưu không khớp SHA-256")
    if manifest["counts"]["task_lists"] != counts_now["task_lists"]:
        raise SystemExit("Số danh sách trong bản sao lưu khác dữ liệu hiện tại")

    junk = urllib.request.Request(
        f"{API}/backup/restore",
        data=b"\0" * (30 * 1024 * 1024),
        method="POST",
        headers={"Content-Type": "application/zip"},
    )
    try:
        urllib.request.urlopen(junk, timeout=120)
    except urllib.error.HTTPError as e:
        if e.code != 400:
            raise SystemExit(f"Gửi file 30 MB: mong đợi HTTP 400, nhận {e.code}") from None
    else:
        raise SystemExit("File rác 30 MB không được bị từ chối")


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
    {
        "setup": setup,
        "verify": verify,
        "add-task": add_task,
        "cleanup": cleanup,
        "backup-check": backup_check,
    }[command](*args)
