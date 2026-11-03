"""GET/PATCH /api/settings (FR-022, FR-048, FR-051)."""

from flask import Blueprint, request

from app.extensions import db
from app.models import Settings
from app.schemas.settings import SettingsOut, SettingsPatch
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
    for field, value in patch.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(settings, field, value)
    bump_revision(db.session)
    db.session.commit()
    return SettingsOut.model_validate(settings, from_attributes=True).model_dump(mode="json")
