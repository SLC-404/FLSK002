"""BLUEPRINT "perfil": cada usuario ve y edita SU perfil y sube sus archivos."""
from flask import Blueprint

bp = Blueprint("perfil", __name__, url_prefix="/perfil")

from app.perfil import routes  # noqa: E402, F401
