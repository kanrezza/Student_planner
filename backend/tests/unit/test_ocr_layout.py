from app.ocr.layout import (
    columns_for_weekdays,
    detect_layout,
    filter_chrome,
    find_week_headers,
    group_cells,
    split_menu_bar,
)
from tests.ocr_helpers import box, load_boxes

SIZE = (2000, 1000)
PITCH = 250


def grid_boxes():
    """Lưới tuần dựng tay: tiêu đề căn giữa, số ngày bên trái chữ "Thứ n"."""
    boxes = [box("Safari   Tệp   Sửa", 20, 4, h=14), box("Th 4 4 thg 11 14:05", 1700, 4, h=14)]
    labels = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
    for i, label in enumerate(labels):
        x = 200 + PITCH * i
        boxes += [box(f"{2 + i:02d}", x - 40, 200, w=30, h=26), box(label, x, 205, w=60)]
    # ô Thứ 2: tiêu đề tên, dòng giờ, mã lớp, phòng, giảng viên
    boxes += [
        box("Giải tích 1", 160, 260, w=110),
        box("06:45 - 09:25 (Tiết 1-3)", 160, 282, w=200),
        box("MAT1101-1-1-26(N01)", 160, 304, w=190),
        box("Phòng: A2-301", 160, 326, w=120),
        box("GV: ThS. Nguyễn Văn An", 160, 348, w=200),
    ]
    # ô Thứ 4 (hai buổi cùng cột, cách nhau xa)
    boxes += [box("Cơ sở dữ liệu", 660, 260), box("13:00 - 15:40", 660, 282)]
    boxes += [box("Vật lý", 660, 600), box("15:45 - 18:25", 660, 622)]
    boxes += [box("8:00", 40, 260, w=40), box("9:00", 40, 330, w=40)]  # nhãn giờ ở lề trái
    boxes += [box("T2", 1950, 300, w=30), box("Tháng 11/2026", 1950, 250, w=150)]  # lịch thu nhỏ
    return boxes


def test_menu_bar_is_split_off_and_dock_removed():
    boxes = grid_boxes() + [box("Mail", 900, 960)]
    menu, rest = split_menu_bar(boxes, SIZE)
    assert {b.text for b in menu} == {"Safari   Tệp   Sửa", "Th 4 4 thg 11 14:05"}
    assert all(b.text not in {"Mail", "Th 4 4 thg 11 14:05"} for b in filter_chrome(boxes, SIZE))
    assert len(rest) == len(boxes) - 2


def test_detect_week_grid_by_headers():
    assert detect_layout(filter_chrome(grid_boxes(), SIZE)) == "week_grid"
    headers = find_week_headers(grid_boxes())
    assert [h.weekday for h in headers] == [1, 2, 3, 4, 5, 6, 7]
    assert [h.day for h in headers] == [2, 3, 4, 5, 6, 7, 8]


def test_header_missing_number_is_inferred_from_position():
    boxes = [
        box(t, 100 + 200 * i, 50, w=60)
        for i, t in enumerate(["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ", "Chú nhật"])
    ]
    assert [h.weekday for h in find_week_headers(boxes)] == [1, 2, 3, 4, 5, 6, 7]


def test_cells_are_grouped_by_column_and_gap():
    content = filter_chrome(grid_boxes(), SIZE)
    headers = find_week_headers(content)
    cells = group_cells(content, headers)
    by_day = {}
    for cell in cells:
        by_day.setdefault(cell.weekday, []).append([line.text for line in cell.lines])
    assert by_day[1] == [
        [
            "Giải tích 1",
            "06:45 - 09:25 (Tiết 1-3)",
            "MAT1101-1-1-26(N01)",
            "Phòng: A2-301",
            "GV: ThS. Nguyễn Văn An",
        ]
    ]
    assert by_day[3] == [["Cơ sở dữ liệu", "13:00 - 15:40"], ["Vật lý", "15:45 - 18:25"]]
    texts = {line.text for cell in cells for line in cell.lines}
    assert "8:00" not in texts and "T2" not in texts and "Tháng 11/2026" not in texts


def test_columns_cover_headers_in_order():
    columns = columns_for_weekdays(find_week_headers(grid_boxes()))
    assert [c.weekday for c in columns] == [1, 2, 3, 4, 5, 6, 7]
    assert all(a.hi == b.lo for a, b in zip(columns, columns[1:], strict=False))


def test_line_split_across_boxes_is_merged():
    boxes = grid_boxes() + [box("13-00", 700, 400, w=45), box("15.40 (Tiết 7-9)", 750, 400, w=140)]
    content = filter_chrome(boxes, SIZE)
    cells = group_cells(content, find_week_headers(content))
    assert any("13-00 15.40 (Tiết 7-9)" in [x.text for x in c.lines] for c in cells)


def test_real_grid_layout():
    boxes, size = load_boxes("real-grid-01")
    content = filter_chrome(boxes, size)
    assert detect_layout(content) == "week_grid"
    headers = find_week_headers(content)
    assert [h.day for h in headers] == [28, 29, 30, 1, 2, 3, 4]


def test_list_layout_by_column_titles():
    titles = ["Môn học", "Thứ", "Tiết", "Phòng", "Giảng viên"]
    boxes = [box(t, 100 + 200 * i, 80, w=100) for i, t in enumerate(titles)]
    boxes += [box("Giải tích", 100, 140), box("2", 300, 140, w=10)]
    assert detect_layout(boxes) == "list"


def test_unknown_when_no_markers():
    assert detect_layout([box("Xin chào", 10, 10), box("Không phải bảng", 10, 50)]) == "unknown"
