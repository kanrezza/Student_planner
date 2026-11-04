"""GET/PATCH /api/settings (FR-022, FR-048, FR-051)."""

from flask import Blueprint, request

from app.extensions import db
from app.models import Settings
from app.schemas.settings import NULLABLE_FIELDS, SettingsOut, SettingsPatch
from app.services import auto_deadlines
from app.services.revision import bump_revision

bp = Blueprint("settings", __name__)


def _settings() -> Settings:
    return db.session.get(Settings, 1)


@bp.get("/settings")
def get_settings():
    return SettingsOut.model_validate(_settings(), from_attributes=True).model_dump(mode="json")


@bp.patch("/settings")
def patch_settings():
    patch = SettingsPatch.model_validate(request.get_json(silent=True) or {})
    settings = _settings()
    changes = {
        k: v
        for k, v in patch.model_dump(exclude_unset=True).items()
        if v is not None or k in NULLABLE_FIELDS
    }
    for field, value in changes.items():
        setattr(settings, field, value)
    if any(
        field.startswith("auto_deadline_") and field not in NULLABLE_FIELDS for field in changes
    ):
        auto_deadlines.reconcile(all_future=True)  # FR-048: áp dụng cho các buổi chưa qua hạn
    bump_revision(db.session)
    db.session.commit()
    return SettingsOut.model_validate(settings, from_attributes=True).model_dump(mode="json")
