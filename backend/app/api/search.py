"""GET /api/search (feature 003 US5, contracts/rest-api.md)."""

from flask import Blueprint, request

from app.api.params import bool_arg, int_arg
from app.services import search as service

bp = Blueprint("search", __name__)


@bp.get("/search")
def search():
    return service.search(
        request.args.get("q", ""),
        bool_arg("include_done", False),
        request.args.get("group") or None,
        int_arg("limit") or service.DEFAULT_LIMIT,
    )
