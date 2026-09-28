"""BLUEPRINT "permisos": CRUD de permisos."""
from flask import Blueprint

bp = Blueprint("permisos", __name__, url_prefix="/permisos")

from app.permisos import routes  # noqa: E402, F401
