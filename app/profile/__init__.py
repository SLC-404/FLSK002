"""BLUEPRINT "profile": each user views and edits THEIR profile and uploads their files."""
from flask import Blueprint

bp = Blueprint("profile", __name__, url_prefix="/profile")

from app.profile import routes  # noqa: E402, F401
