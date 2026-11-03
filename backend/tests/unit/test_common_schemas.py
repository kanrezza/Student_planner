from datetime import time

import pytest
from pydantic import Field, ValidationError

from app.schemas.common import HHMM, ApiModel, vi_error_messages


class Row(ApiModel):
    name: str = Field(min_length=1, max_length=300)
    end_time: HHMM


class Rows(ApiModel):
    rows: list[Row]


def errors_of(model, data) -> dict[str, str]:
    with pytest.raises(ValidationError) as exc:
        model.model_validate(data)
    return vi_error_messages(exc.value.errors())


def test_hhmm_parses_and_serializes():
    row = Row.model_validate({"name": "A", "end_time": "07:30"})
    assert row.end_time == time(7, 30)
    assert row.model_dump(mode="json")["end_time"] == "07:30"


@pytest.mark.parametrize("bad", ["7:30", "24:00", "07:60", "0730", ""])
def test_hhmm_rejects_bad_values_with_vietnamese_message(bad):
    fields = errors_of(Row, {"name": "A", "end_time": bad})
    assert fields["end_time"] == "Giờ phải có dạng HH:MM (ví dụ 07:30)"


def test_nested_list_paths_use_brackets():
    data = {"rows": [{"name": "A", "end_time": "07:30"}] * 2 + [{"name": "B", "end_time": "x"}]}
    assert "rows[2].end_time" in errors_of(Rows, data)


def test_blank_string_after_strip_is_reported_in_vietnamese():
    fields = errors_of(Row, {"name": "   ", "end_time": "07:30"})
    assert fields["name"] == "Trường này không được để trống"


def test_too_long_string_is_reported_in_vietnamese():
    fields = errors_of(Row, {"name": "x" * 301, "end_time": "07:30"})
    assert fields["name"] == "Không được dài quá 300 ký tự"


def test_missing_and_extra_fields():
    fields = errors_of(Row, {"unknown": 1})
    assert fields["name"] == "Trường này là bắt buộc"
    assert fields["unknown"] == "Trường không được hỗ trợ"
