"""Trạng thái cục bộ của agent: ID lịch/danh sách do app tạo và fingerprint lần ghi gần nhất.

Ghi nguyên tử (file tạm rồi đổi tên) để tắt đột ngột không làm hỏng file (constitution V).
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path.home() / "Library/Application Support/LichHocAgent/state.json"


@dataclass
class State:
    path: Path = DEFAULT_PATH
    calendar_id: str | None = None
    reminder_list_id: str | None = None
    fingerprints: dict[str, str] = field(default_factory=dict)
    item_keys: dict[str, str] = field(default_factory=dict)  # calendarItemIdentifier → sync_key
    last_revision: int = 0

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "State":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls(path=Path(path))
        return cls(
            path=Path(path),
            calendar_id=data.get("calendar_id"),
            reminder_list_id=data.get("reminder_list_id"),
            fingerprints=data.get("fingerprints", {}),
            item_keys=data.get("item_keys", {}),
            last_revision=data.get("last_revision", 0),
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        payload = {
            "calendar_id": self.calendar_id,
            "reminder_list_id": self.reminder_list_id,
            "fingerprints": self.fingerprints,
            "item_keys": self.item_keys,
            "last_revision": self.last_revision,
        }
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def clear(self) -> None:
        self.calendar_id = self.reminder_list_id = None
        self.fingerprints, self.item_keys = {}, {}
        self.save()
