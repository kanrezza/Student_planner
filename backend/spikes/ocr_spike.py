"""SPIKE S1 (task T010, research R2): EasyOCR tiếng Việt chạy offline có đọc đủ tốt ảnh thời khoá biểu?

Đo trên mỗi ảnh và mỗi cấu hình:
- thời gian nhận diện, số khối chữ, độ tin cậy trung bình;
- với từng trường mong đợi (tên môn, giờ, mã lớp, phòng, giảng viên): có tìm thấy CHÍNH XÁC trong kết
  quả OCR không (so sánh sau chuẩn hoá NFC + gộp khoảng trắng), và độ giống gần nhất (rapidfuzz);
- "dòng đọc đúng hoàn toàn" = mọi trường của buổi học đều tìm thấy chính xác. Đây là CẬN TRÊN của tỉ lệ
  SC-011, vì chưa có bộ ghép bố cục (layout parser) — parser chỉ có thể làm xấu đi, không làm tốt hơn,
  trừ khi sửa lỗi bằng tri thức (đối chiếu ca, so khớp tên môn đã có);
- có đọc được dấu hiệu tháng/năm (tiêu đề lịch thu nhỏ, ngày giờ trên thanh menu) không.

Chạy trong image backend (model đã có sẵn, không cần mạng):
  docker run --rm --network none -v "$PWD/samples:/samples:ro" -v "$PWD/backend/spikes:/spikes" \
      --entrypoint python lichhoc-backend:spike /spikes/ocr_spike.py /samples/synthetic
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import easyocr
import numpy as np
from PIL import Image, ImageEnhance
from rapidfuzz import fuzz

MODEL_DIR = os.environ.get("EASYOCR_MODEL_DIR", "/opt/easyocr-models")
FIELDS = ["name", "time_label", "class_code", "room", "lecturer"]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def preprocess(img: Image.Image, enhance: bool, factor: float = 1.5) -> np.ndarray:
    img = img.convert("RGB")
    if enhance:
        img = img.resize((int(img.width * factor), int(img.height * factor)), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.4)
    return np.array(img)


def expected_strings(row: dict) -> dict[str, str]:
    return {
        "name": row["name"],
        "time_label": row["time_label"],
        "class_code": row["class_code"],
        "room": f"Phòng: {row['room']}",
        "lecturer": f"GV: {row['lecturer']}",
    }


def best_match(target: str, lines: list[str]) -> tuple[bool, float, str]:
    """Tìm target trong các dòng OCR. Cho phép target bị xuống dòng: ghép 2 dòng liền nhau."""
    t = norm(target)
    candidates = lines + [f"{a} {b}" for a, b in zip(lines, lines[1:], strict=False)]
    exact = any(t == norm(c) or t in norm(c) for c in candidates)
    score, best = 0.0, ""
    for c in candidates:
        s = fuzz.ratio(t, norm(c))
        if s > score:
            score, best = s, c
    return exact, score, best


def run(
    reader: easyocr.Reader, image_path: Path, expected: dict, decoder: str, enhance: bool
) -> dict:
    arr = preprocess(Image.open(image_path), enhance)
    t0 = time.perf_counter()
    results = reader.readtext(arr, decoder=decoder, paragraph=False)
    elapsed = time.perf_counter() - t0

    # Sắp các khối theo vị trí (trên→dưới, trái→phải) để ghép dòng bị xuống hàng.
    boxes = sorted(results, key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
    lines = [norm(r[1]) for r in boxes]
    confs = [float(r[2]) for r in results]

    field_hits = {f: 0 for f in FIELDS}
    field_scores = {f: [] for f in FIELDS}
    misses = []
    rows_ok = 0
    for row in expected["rows"]:
        row_ok = True
        for field, target in expected_strings(row).items():
            exact, score, best = best_match(target, lines)
            field_hits[field] += exact
            field_scores[field].append(score)
            if not exact:
                row_ok = False
                misses.append(
                    {
                        "field": field,
                        "expected": target,
                        "closest": best,
                        "similarity": round(score, 1),
                    }
                )
        rows_ok += row_ok

    n = len(expected["rows"])
    month_hint = expected["mini_calendar_title"]
    menu_hint = expected["menu_bar_text"]
    return {
        "image": image_path.name,
        "decoder": decoder,
        "enhance": enhance,
        "seconds": round(elapsed, 1),
        "boxes": len(results),
        "mean_conf": round(sum(confs) / max(len(confs), 1), 3),
        "rows": n,
        "rows_fully_exact": rows_ok,
        "rows_fully_exact_pct": round(100 * rows_ok / n, 1),
        "field_exact_pct": {f: round(100 * field_hits[f] / n, 1) for f in FIELDS},
        "field_mean_similarity": {f: round(sum(v) / n, 1) for f, v in field_scores.items()},
        "month_hint_found": best_match(month_hint, lines)[0],
        "menu_bar_date_found": best_match(menu_hint, lines)[0],
        "misses": misses,
        "ocr_lines": lines,
    }


# ---------------------------------------------------------------------------------------------------
# Đánh giá lần 2: ước lượng gần SC-011 hơn — gom khối theo Ô (cột từ tiêu đề "Thứ 2…CN", ô = các khối
# liền nhau theo chiều dọc) và chuẩn hoá các lỗi CÓ QUY LUẬT (research R3 bước 5). Tên môn KHÔNG được
# sửa dấu (lỗi dấu vẫn tính là sai), vì chưa có danh sách môn để so khớp ở lần nhập đầu tiên.
# ---------------------------------------------------------------------------------------------------
SHIFTS = {
    "1-3": ("06:45", "09:25"),
    "4-6": ("09:35", "12:10"),
    "7-9": ("13:00", "15:40"),
    "10-12": ("15:45", "18:25"),
    "1-6": ("06:45", "12:10"),
    "7-12": ("13:00", "18:25"),
}
WEEKDAY_HEADERS = ["thứ 2", "thứ 3", "thứ 4", "thứ 5", "thứ 6", "thứ 7", "cn"]
TIME_RE = re.compile(r"(\d{1,2})\s*[:.*,]\s*(\d{2})")
TIET_RE = re.compile(r"Ti\S{0,3}t\s*(\d{1,2})\s*-\s*(\d{1,2})", re.I)


def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def parse_time(text: str) -> tuple[str | None, str | None, str]:
    """Trả (start, end, nguồn). Ưu tiên giờ đọc được; khớp ca ±5 phút thì lấy giờ ca (FR-041)."""
    times = [f"{int(h):02d}:{m}" for h, m in TIME_RE.findall(text)]
    tiet = TIET_RE.search(text)
    tiet_key = f"{tiet.group(1)}-{tiet.group(2)}" if tiet else None
    if len(times) >= 2:
        start, end = times[0], times[1]
        for s, e in SHIFTS.values():
            if (
                abs(to_minutes(start) - to_minutes(s)) <= 5
                and abs(to_minutes(end) - to_minutes(e)) <= 5
            ):
                return s, e, "giờ khớp ca"
        if (
            tiet_key in SHIFTS
        ):  # giờ đọc lệch nhưng tiết đọc được → tin tiết, đánh dấu chưa chắc chắn
            return *SHIFTS[tiet_key], "theo tiết (giờ đọc lệch)"
        return start, end, "giờ tuỳ chỉnh"
    if tiet_key in SHIFTS:
        return *SHIFTS[tiet_key], "theo tiết"
    return None, None, "không đọc được"


def fix_class_code(text: str) -> str:
    text = re.sub(r"\(N[O0o](\d)\)", r"(N0\1)", text)
    return re.sub(r"^([A-Z]{3})[I1l](\d{3})", r"\g<1>1\2", text)


def header_key(text: str) -> str | None:
    """'Thứ 2', 'Thứ2', 'Thu 2', 'CN' → khoá cột (OCR hay mất dấu hoặc dính chữ)."""
    t = re.sub(r"\s+", "", norm(text).lower())
    m = re.fullmatch(r"th\S?([2-7])", t)
    if m:
        return f"thứ {m.group(1)}"
    return "cn" if t in {"cn", "chủnhật"} else None


def group_cells(results: list) -> list[tuple[int, list[str]]]:
    """Cột = tiêu đề Thứ gần nhất BÊN TRÁI mép trái khối; bỏ khối nằm trái lưới (nhãn giờ) hoặc phải
    lưới (lịch thu nhỏ). Ô = các khối liền nhau theo chiều dọc; trong một dòng sắp theo x."""
    headers = {}
    for box, text, _ in results:
        key = header_key(text)
        if key and key not in headers:  # lấy lần xuất hiện đầu (lưới tuần nằm trên lịch thu nhỏ)
            headers[key] = (box[0][0], box[0][1])
    if len(headers) < 5:
        return []
    cols = sorted((x, WEEKDAY_HEADERS.index(k)) for k, (x, _) in headers.items())
    header_y = max(y for _, y in headers.values())
    col_width = (cols[-1][0] - cols[0][0]) / max(len(cols) - 1, 1)
    # Tiêu đề nằm lệch vào trong cột (sau số ngày "02"), nên mép trái cột ≈ x tiêu đề − 0.4 cột.
    lefts = [(x - 0.4 * col_width, wd) for x, wd in cols]
    grid_left, grid_right = lefts[0][0], lefts[-1][0] + col_width
    columns: dict[int, list] = {}
    for box, text, _ in results:
        x0, y0 = box[0]
        y1 = box[2][1]
        if y0 <= header_y + 5 or x0 < grid_left or x0 > grid_right:
            continue
        wd = max((c for c in lefts if c[0] <= x0 + 2), default=lefts[0])[1]
        columns.setdefault(wd, []).append((y0, y1, x0, norm(text)))
    cells = []
    for wd, items in columns.items():
        # gộp các khối cùng dòng (|Δy| < nửa chiều cao) rồi sắp theo x
        items.sort(key=lambda t: t[0])
        lines: list[list] = []
        for it in items:
            if lines and abs(it[0] - lines[-1][0][0]) < 0.5 * (it[1] - it[0]):
                lines[-1].append(it)
            else:
                lines.append([it])
        cell, last_bottom, line_h = [], None, None
        for line in lines:
            line.sort(key=lambda t: t[2])
            y0, y1 = min(t[0] for t in line), max(t[1] for t in line)
            if cell and y0 - last_bottom > 1.2 * (line_h or (y1 - y0)):
                cells.append((wd, cell))
                cell = []
            cell.append(" ".join(t[3] for t in line))
            last_bottom, line_h = y1, y1 - y0
        if cell:
            cells.append((wd, cell))
    return cells


def parse_cell(wd: int, lines: list[str]) -> dict:
    joined = " ".join(lines)
    start, end, source = parse_time(joined)
    time_idx = next(
        (i for i, ln in enumerate(lines) if TIME_RE.search(ln) or TIET_RE.search(ln)), None
    )
    name = " ".join(lines[:time_idx]) if time_idx else lines[0]
    rest = lines[time_idx + 1 :] if time_idx is not None else lines[1:]
    code = next((fix_class_code(ln) for ln in rest if re.search(r"[A-Z]{3}.?\d{3}", ln)), None)
    room_i = next((i for i, ln in enumerate(rest) if re.match(r"Ph\S{0,3}ng\s*:", ln)), None)
    gv_i = next((i for i, ln in enumerate(rest) if ln.startswith("GV")), None)
    room = re.sub(r"^Ph\S{0,3}ng\s*:\s*", "", rest[room_i]) if room_i is not None else None
    lecturer = None
    if gv_i is not None:
        lecturer = re.sub(r"^GV\s*:\s*", "", " ".join(rest[gv_i:]))
    return {
        "weekday": wd + 1,
        "name": name,
        "start_time": start,
        "end_time": end,
        "time_source": source,
        "class_code": code,
        "room": room,
        "lecturer": lecturer,
    }


def evaluate_parsed(results: list, expected: dict) -> dict:
    parsed = [parse_cell(wd, lines) for wd, lines in group_cells(results)]
    fields = ["name", "start_time", "end_time", "class_code", "room", "lecturer"]
    ok_rows, per_field, details = 0, {f: 0 for f in fields}, []
    for row in expected["rows"]:
        exp = {
            "name": row["name"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "class_code": row["class_code"],
            "room": row["room"],
            "lecturer": row["lecturer"],
        }
        same_day = [p for p in parsed if p["weekday"] == row["weekday"]]
        best = max(same_day, key=lambda p: fuzz.ratio(exp["name"], p["name"] or ""), default=None)
        wrong = [f for f in fields if not best or norm(str(best[f] or "")) != norm(exp[f])]
        for f in fields:
            per_field[f] += f not in wrong
        ok_rows += not wrong
        details.append(
            {
                "expected_name": exp["name"],
                "wrong_fields": wrong,
                "got": {f: best[f] for f in fields} if best else None,
                "time_source": best["time_source"] if best else None,
            }
        )
    n = len(expected["rows"])
    return {
        "cells_found": len(parsed),
        "rows_fully_correct": ok_rows,
        "rows_fully_correct_pct": round(100 * ok_rows / n, 1),
        "field_correct_pct": {f: round(100 * v / n, 1) for f, v in per_field.items()},
        "details": details,
    }


def main_parsed(sample_dir: Path, out_dir: Path) -> None:
    reader = easyocr.Reader(
        ["vi", "en"],
        gpu=False,
        model_storage_directory=MODEL_DIR,
        download_enabled=False,
        verbose=False,
    )
    report = []
    for exp_path in sorted(sample_dir.glob("*.expected.json")):
        expected = json.loads(exp_path.read_text(encoding="utf-8"))
        img = Image.open(sample_dir / expected["image"])
        # Quy tắc rút ra từ spike: ảnh màn hình thường (< 2000 px) phóng to ×2 trước khi OCR.
        low_res = img.width < 2000
        arr = preprocess(img, enhance=low_res, factor=2.0)
        t0 = time.perf_counter()
        results = reader.readtext(arr, paragraph=False)
        elapsed = round(time.perf_counter() - t0, 1)
        ev = evaluate_parsed(results, expected)
        ev.update(image=expected["image"], seconds=elapsed, upscaled=low_res)
        report.append(ev)
        print(
            f"{ev['image']:<14} {elapsed:>5}s  phóng_to={low_res!s:<5} ô={ev['cells_found']}  "
            f"đúng hoàn toàn={ev['rows_fully_correct']}/{len(expected['rows'])} "
            f"({ev['rows_fully_correct_pct']}%)  trường={ev['field_correct_pct']}"
        )
        for d in ev["details"]:
            if d["wrong_fields"]:
                print(f"    ✗ {d['expected_name']}: sai {d['wrong_fields']} → {d['got']}")
    (out_dir / "ocr_spike_parsed.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    sample_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/samples/synthetic")
    if "--parsed" in sys.argv:
        out_dir = Path(__file__).parent / "results"
        out_dir.mkdir(exist_ok=True)
        main_parsed(sample_dir, out_dir)
        return
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)

    t0 = time.perf_counter()
    reader = easyocr.Reader(
        ["vi", "en"],
        gpu=False,
        model_storage_directory=MODEL_DIR,
        download_enabled=False,
        verbose=False,
    )
    print(f"Nạp model: {time.perf_counter() - t0:.1f}s (download_enabled=False)")

    configs = [("greedy", False), ("beamsearch", False), ("greedy", True)]
    all_results = []
    for exp_path in sorted(sample_dir.glob("*.expected.json")):
        expected = json.loads(exp_path.read_text(encoding="utf-8"))
        image_path = sample_dir / expected["image"]
        for decoder, enhance in configs:
            res = run(reader, image_path, expected, decoder, enhance)
            all_results.append(res)
            print(
                f"{res['image']:<14} {decoder:<10} enhance={enhance!s:<5} "
                f"{res['seconds']:>5}s  conf={res['mean_conf']:.2f}  "
                f"đúng hoàn toàn={res['rows_fully_exact']}/{res['rows']} "
                f"({res['rows_fully_exact_pct']}%)  trường={res['field_exact_pct']}  "
                f"tháng={res['month_hint_found']} menu={res['menu_bar_date_found']}"
            )

    (out_dir / "ocr_spike_results.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Chi tiết: {out_dir / 'ocr_spike_results.json'}")


if __name__ == "__main__":
    main()
