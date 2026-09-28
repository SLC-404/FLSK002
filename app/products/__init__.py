"""BLUEPRINT "products": products CRUD (practice 9.7)."""
from flask import Blueprint

bp = Blueprint("products", __name__, url_prefix="/products")

from app.products import routes  # noqa: E402, F401
