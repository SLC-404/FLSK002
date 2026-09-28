from flask import render_template
from flask_login import current_user, login_required

from app.main import bp
from app.utils.decoradores import permiso_requerido


@bp.get("/")
def inicio():
    """Página pública: cualquiera puede verla."""
    return render_template("main/inicio.html")


@bp.get("/panel")
@login_required                  # ← solo usuarios con sesión iniciada (como middleware('auth'))
@permiso_requerido("ver-inicio")  # ← y que su rol tenga el permiso
def panel():
    """Página privada: si no has iniciado sesión, te manda al login."""
    return render_template("main/panel.html", usuario=current_user)
