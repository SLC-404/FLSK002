"""BLUEPRINT "roles": roles CRUD (and the permissions of each role)."""
from flask import Blueprint

bp = Blueprint("roles", __name__, url_prefix="/roles")

from app.roles import routes  # noqa: E402, F401
