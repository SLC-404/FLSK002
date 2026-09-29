"""BLUEPRINT "api": REST API in JSON (for Vue/React/mobile apps or other systems).

Same data as the web pages, but:
  - it receives and returns JSON (not HTML forms)
  - it uses HTTP methods: GET (read), POST (create), PUT (update), DELETE (delete)
  - it answers with status codes: 200 OK, 201 Created, 204 No Content,
    400/422 bad data, 401 no key, 404 not found
"""
from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from app.api import routes  # noqa: E402, F401
