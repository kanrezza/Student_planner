"""Sinh file giả lập cho test đính kèm (feature 005); không dùng tài liệu thật.

Chạy trong container: docker compose run --rm -v "$PWD:/repo" backend python /repo/samples/synthetic/make_attachment_fixtures.py
"""

import io
import zipfile
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "tests"
    / "fixtures"
    / "attachments"
)


def office(parts: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, text in parts.items():
            zf.writestr(name, text)
    return buffer.getvalue()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 60, 60)).save(image, "PNG")
    (OUT / "anh-nho.png").write_bytes(image.getvalue())

    pdf = io.BytesIO()
    page = canvas.Canvas(pdf, pagesize=A4)
    for number in (1, 2):
        page.drawString(72, 750, f"De cuong gia lap - trang {number}")
        page.showPage()
    page.save()
    (OUT / "de-cuong.pdf").write_bytes(pdf.getvalue())

    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
        'package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>'
    )
    (OUT / "bai-tap.docx").write_bytes(
        office({"[Content_Types].xml": content_types, "word/document.xml": "<w/>"})
    )
    (OUT / "bang-diem.xlsx").write_bytes(
        office({"[Content_Types].xml": content_types, "xl/workbook.xml": "<w/>"})
    )
    (OUT / "rong.txt").write_bytes(b"")
    (OUT / "chay-thu.command").write_text("#!/bin/sh\necho gia lap\n")
    (OUT / "gia-mao.png").write_text("<html><script>alert(1)</script></html>")
    (OUT / "ve.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>'
    )


if __name__ == "__main__":
    main()
