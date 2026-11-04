"""SPIKE S1 lần 2 (T010 → kiểm chứng bằng ảnh THẬT): EasyOCR đọc đúng bao nhiêu trường trên ảnh thật?

Đáp án (`real/*.expected.json`) do người đọc ảnh viết tay. Chỉ tính các ô nhìn thấy đủ trong ảnh; mỗi dòng có `region` (px ảnh gốc) khoanh vùng ô.
Một trường tính là ĐÚNG khi mọi từ của đáp án có trong các khối chữ nằm trong vùng của ô (sau chuẩn hoá
NFC, chữ thường, giờ '.'→':', bỏ dấu '-' rời). "Nguyên văn" = từ giống hệt; "gần đúng" = từ giống ≥ 80%
(lỗi 1–2 ký tự, người dùng sửa được ở bảng xem trước).
Đây là cận trên của SC-011/SC-020, vì chưa có bộ ghép bố cục.

  docker run --rm --network none -v "$PWD/samples:/samples:ro" -v "$PWD/backend/spikes:/spikes" \
      --entrypoint python lichhoc-backend:latest /spikes/real_spike.py
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
from PIL import Image
from rapidfuzz import fuzz

MODEL_DIR = os.environ.get("EASYOCR_MODEL_DIR", "/opt/easyocr-models")
HERE = Path(__file__).parent


def norm(text: str) -> str:
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().lower()
    return re.sub(r"(?<=\d)[.:,-](?=\d{2}\b)", ":", text)


def tokens(text: str) -> list[str]:
    """Tách từ sau chuẩn hoá; bỏ dấu gạch rời (OCR hay làm rơi) và dấu ngoặc."""
    return [t for t in re.split(r"[\s()]+", norm(text)) if t and t != "-"]


def field_ok(target: str, bag: list[str]) -> tuple[bool, bool]:
    """(đúng nguyên văn, đúng gần đúng) — mọi từ của đáp án phải có trong các khối thuộc ô."""
    remaining_exact = list(bag)
    remaining_fuzzy = list(bag)
    exact = fuzzy = True
    for tok in tokens(target):
        hit = next((b for b in remaining_exact if tok == b or (len(tok) >= 3 and tok in b)), None)
        if hit is not None:
            remaining_exact.remove(hit)
        else:
            exact = False
        best = max(remaining_fuzzy, key=lambda b: fuzz.partial_ratio(tok, b), default=None)
        if best is not None and fuzz.partial_ratio(tok, best) >= 80:
            remaining_fuzzy.remove(best)
        else:
            fuzzy = False
    return exact, fuzzy


def main() -> None:
    reader = easyocr.Reader(
        ["vi", "en"],
        gpu=False,
        model_storage_directory=MODEL_DIR,
        download_enabled=False,
        verbose=False,
    )
    report = []
    for exp_path in sorted((HERE / "real").glob("*.expected.json")):
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        img = Image.open(Path("/samples") / exp["image"]).convert("RGB")
        scale = float(os.environ.get("SCALE", "1.0"))
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        t0 = time.perf_counter()
        res = reader.readtext(np.array(img), paragraph=False)
        sec = round(time.perf_counter() - t0, 1)
        totals: dict[str, list[bool]] = {}
        fuzzy_totals: dict[str, list[bool]] = {}
        rows_ok = rows_fuzzy = 0
        misses = []
        for row in exp["rows"]:
            x0, y0, x1, y1 = row["region"]
            bag = []
            for box, text, _conf in res:
                cx = sum(p[0] for p in box) / 4 / scale
                cy = sum(p[1] for p in box) / 4 / scale
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    bag += tokens(text)
            ok = ok_f = True
            for field, target in row["fields"].items():
                exact, fuzzy = field_ok(target, bag)
                totals.setdefault(field, []).append(exact)
                fuzzy_totals.setdefault(field, []).append(fuzzy)
                ok &= exact
                ok_f &= fuzzy
                if not exact:
                    missing = [t for t in tokens(target) if not any(t in b for b in bag)]
                    misses.append((row["fields"].get("name", "?"), field, "thiếu từ:", missing))
            rows_ok += ok
            rows_fuzzy += ok_f
        n = len(exp["rows"])
        fields_ok = sum(sum(v) for v in totals.values())
        fields_all = sum(len(v) for v in totals.values())
        entry = {
            "image": exp["image"][:12] + "…",
            "kind": exp["kind"],
            "seconds": sec,
            "boxes": len(res),
            "rows": n,
            "rows_exact": rows_ok,
            "rows_exact_pct": round(100 * rows_ok / n, 1),
            "rows_fuzzy": rows_fuzzy,
            "fields_exact_pct": round(100 * fields_ok / fields_all, 1),
            "per_field_pct": {f: round(100 * sum(v) / len(v)) for f, v in totals.items()},
            "misses": misses,
        }
        report.append(entry)
        print(json.dumps({k: v for k, v in entry.items() if k != "misses"}, ensure_ascii=False))
        for m in misses:
            print("   ✗", m)
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "real_spike.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    all_rows = sum(e["rows"] for e in report)
    ok_rows = sum(e["rows_exact"] for e in report)
    ok_fuzzy = sum(e["rows_fuzzy"] for e in report)
    print(f"TỔNG: đúng nguyên văn {ok_rows}/{all_rows} = {100 * ok_rows / all_rows:.1f}%")
    print(
        f"      đúng gần đúng (sai ≤ 1–2 ký tự/từ) {ok_fuzzy}/{all_rows} = {100 * ok_fuzzy / all_rows:.1f}%"
    )


if __name__ == "__main__":
    sys.exit(main())
