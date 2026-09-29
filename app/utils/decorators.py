"""PERMISSION DECORATORS (the "middleware").

Normal usage (by PERMISSION, recommended):
    @bp.get("/users")
    @login_required                        # 1st: is the user logged in?
    @permission_required("view-users")     # 2nd: does their role have that permission?
    def index(): ...

Laravel (Spatie) equivalent: ->middleware(['auth', 'permission:view-users'])

role_required("admin") stays in case you ever need to check the ROLE directly.
"""
from functools import wraps

from flask import abort, current_app, jsonify, request
from flask_login import current_user


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(*roles):
                abort(403)   # forbidden -> templates/errors/403.html
            return func(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def api_key_required(func):
    """For the JSON API: checks the "X-API-Key" header against API_KEY from .env.
    APIs don't use the login session/cookies: each request brings its own key (or a token)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("API_KEY")
        if expected and request.headers.get("X-API-Key") != expected:
            return jsonify(error="API key inválida o faltante"), 401
        return func(*args, **kwargs)
    return wrapper
