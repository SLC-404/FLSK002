"""DECORADORES DE PERMISOS (el "middleware de roles").

Uso:
    @bp.get("/usuarios")
    @login_required               # 1° ¿inició sesión?
    @rol_requerido("admin")       # 2° ¿tiene el rol?
    def lista(): ...

Equivalente en Laravel: ->middleware(['auth', 'role:admin'])
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def rol_requerido(*roles):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.tiene_rol(*roles):
                abort(403)   # prohibido -> templates/errores/403.html
            return funcion(*args, **kwargs)
        return envoltura
    return decorador
