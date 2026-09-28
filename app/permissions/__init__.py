"""BLUEPRINT "permissions": permissions CRUD."""
from flask import Blueprint

bp = Blueprint("permissions", __name__, url_prefix="/permissions")

from app.permissions import routes  # noqa: E402, F401
