"""DECORADORES DE PERMISOS (el "middleware").

Uso normal (por PERMISO, lo recomendado):
    @bp.get("/usuarios")
    @login_required                        # 1° ¿inició sesión?
    @permiso_requerido("ver-usuarios")     # 2° ¿su rol tiene ese permiso?
    def lista(): ...

Equivalente en Laravel (Spatie): ->middleware(['auth', 'permission:ver-usuarios'])

rol_requerido("admin") se queda por si algún día necesitas checar el ROL directo.
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


def permiso_requerido(permiso):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.puede(permiso):
                abort(403)
            return funcion(*args, **kwargs)
        return envoltura
    return decorador
