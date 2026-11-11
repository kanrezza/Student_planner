"""Mở PDF từ bytes trong bộ nhớ và lấy từ + đường kẻ bảng của từng trang (R1, R2, R14).

Không ghi đĩa, không log nội dung (R6, SC-006): chỉ trả cấu trúc hình học và chữ cho tầng sau, nơi
phần đầu trang (họ tên, mã sinh viên…) bị bỏ ngay.
"""

import io
from dataclasses import dataclass, field

import pdfplumber

MAX_PAGES = 20
X_TOLERANCE = 1.5  # khoảng cách giữa hai từ trong file thật ≈ 2,1 pt (R2)


class PdfImportError(Exception):
    """Lỗi đọc PDF có mã (contracts/rest-api.md): `status` là mã HTTP."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.top + self.bottom) / 2


@dataclass
class PageData:
    width: float
    height: float
    words: list[Word]
    # Ranh giới hàng của bảng lớn nhất trang (top, bottom) và hoành độ các đường kẻ dọc; rỗng nếu
    # trang không có đường kẻ (khi đó tầng bố cục dùng cách dự phòng theo chữ).
    row_bands: list[tuple[float, float]] = field(default_factory=list)
    vertical_edges: list[float] = field(default_factory=list)


def _largest_table(page):
    tables = page.find_tables()
    if not tables:
        return None
    return max(tables, key=lambda t: (t.bbox[2] - t.bbox[0]) * (t.bbox[3] - t.bbox[1]))


def _page_data(page) -> PageData:
    words = [
        Word(w["text"], w["x0"], w["x1"], w["top"], w["bottom"])
        for w in page.extract_words(x_tolerance=X_TOLERANCE)
    ]
    data = PageData(float(page.width), float(page.height), words)
    table = _largest_table(page)
    if table is not None:
        bands = sorted({(round(r[1], 1), round(r[3], 1)) for r in (row.bbox for row in table.rows)})
        edges = sorted({round(x, 1) for row in table.rows for x in _cell_edges(row)})
        if len(bands) >= 2 and len(edges) >= 4:
            data.row_bands = bands
            data.vertical_edges = edges
    return data


def _cell_edges(row) -> list[float]:
    return [c[0] for c in row.cells if c] + [c[2] for c in row.cells if c]


def read_pdf(data: bytes) -> list[PageData]:
    """Đọc mọi trang. Ném `PdfImportError` theo thứ tự kiểm tra của R14."""
    if data[:1024].find(b"%PDF-") < 0:
        raise PdfImportError(415, "unsupported_file", "File không phải PDF")
    if b"/Encrypt" in data:
        raise PdfImportError(
            422, "pdf_encrypted", "File PDF có mật khẩu. Hãy mở khoá file rồi nhập lại."
        )
    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 — pdfminer ném nhiều loại lỗi khác nhau
        raise _classify(exc) from None
    try:
        if len(pdf.pages) > MAX_PAGES:
            raise PdfImportError(
                422,
                "pdf_too_long",
                f"File PDF dài quá {MAX_PAGES} trang, không phải thời khoá biểu.",
            )
        try:
            pages = [_page_data(page) for page in pdf.pages]
        except PdfImportError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from None
    finally:
        pdf.close()
    if not any(page.words for page in pages):
        raise PdfImportError(
            422,
            "pdf_no_text",
            "File PDF không có chữ (có thể là ảnh quét). Hãy dùng chức năng nhập từ ảnh.",
        )
    return pages


def _classify(exc: Exception) -> PdfImportError:
    text = f"{type(exc).__name__} {exc}".lower()
    if "password" in text or "encrypt" in text:
        return PdfImportError(
            422, "pdf_encrypted", "File PDF có mật khẩu. Hãy mở khoá file rồi nhập lại."
        )
    return PdfImportError(422, "pdf_unreadable", "Không đọc được file PDF (file có thể bị hỏng).")
