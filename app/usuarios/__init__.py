"""BLUEPRINT "usuarios": CRUD de usuarios (solo administradores)."""
from flask import Blueprint

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

from app.usuarios import routes  # noqa: E402, F401
