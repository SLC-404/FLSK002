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

from flask import abort
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
