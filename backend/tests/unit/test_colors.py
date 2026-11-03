from app.services.colors import PALETTE, display_color, next_color


def test_palette_has_12_codes():
    assert PALETTE == [f"c{i:02d}" for i in range(1, 13)]


def test_next_color_first_unused_in_order():
    assert next_color([]) == "c01"
    assert next_color(["c01", "c02"]) == "c03"


def test_next_color_least_used_when_all_used():
    used = PALETTE + ["c01", "c02"]  # c01, c02 dùng 2 lần; còn lại 1 lần
    assert next_color(used) == "c03"


def test_next_color_ignores_unknown_codes():
    assert next_color(["xyz"]) == "c01"


def test_display_color_prefers_first_tag():
    assert display_color(["c07", "c09"], fallback="c01") == "c07"
    assert display_color([], fallback="c01") == "c01"
