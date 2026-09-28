"""BLUEPRINT "main": general pages (home and dashboard)."""
from flask import Blueprint

bp = Blueprint("main", __name__)

from app.main import routes  # noqa: E402, F401
