"""BLUEPRINT "categories": categories CRUD (practice 9.7)."""
from flask import Blueprint

bp = Blueprint("categories", __name__, url_prefix="/categories")

from app.categories import routes  # noqa: E402, F401
