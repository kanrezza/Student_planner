"""Dữ liệu gửi lên `POST /api/imports/timetable-pdf/commit` (contracts/rest-api.md, feature 004)."""

import datetime as dt
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ApiModel
from app.schemas.subjects import ScheduleIn


class PdfScheduleIn(ScheduleIn):
    # Giao diện gửi lại nguyên quy tắc xem trước (kèm trường chỉ để hiển thị): bỏ qua trường thừa.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    save_periods: bool = False


class SemesterChoiceIn(ApiModel):
    choice: Literal["use", "extend", "create"]
    semester_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: dt.date | None = None
    end_date: dt.date | None = None

    @model_validator(mode="after")
    def _needs(self):
        if self.choice in ("use", "extend") and self.semester_id is None:
            raise ValueError("Thiếu học kỳ được chọn")
        if self.choice == "create" and not (self.name and self.start_date and self.end_date):
            raise ValueError("Học kỳ mới cần tên, ngày bắt đầu và ngày kết thúc")
        if self.choice == "extend" and not (self.start_date and self.end_date):
            raise ValueError("Cần ngày bắt đầu và kết thúc mới của học kỳ")
        return self


class PdfSubjectIn(ApiModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    existing_subject_id: int | None = None
    course_code: str | None = None
    name: str = Field(min_length=1, max_length=200)
    class_code: str | None = None
    credits: int | None = Field(default=None, ge=0, le=30)
    tag_ids: list[int] = []
    schedules: list[PdfScheduleIn] = Field(min_length=1)


class TimetableCommitIn(ApiModel):
    semester: SemesterChoiceIn
    subjects: list[PdfSubjectIn] = Field(min_length=1)
