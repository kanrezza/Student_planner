from flask import Blueprint
from sqlalchemy import text

from app.extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))  # kiểm tra kết nối database
    return {"status": "ok"}
