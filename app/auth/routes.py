"""RUTAS DE AUTENTICACIÓN

Flask-Login nos da:
  login_user(usuario)   -> inicia la sesión     (Auth::login)
  logout_user()         -> cierra la sesión     (Auth::logout)
  current_user          -> el usuario actual    (Auth::user)
  @login_required       -> protege una ruta     (middleware 'auth')
"""
from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import bp
from app.auth.forms import LoginForm, RegistroForm
from app.extensions import db
from app.models import Rol, Usuario


def es_url_segura(destino):
    """Solo permite redirigir a rutas de NUESTRA app (que empiecen con /).
    Evita que alguien mande un link tipo /auth/login?next=https://sitio-malo.com"""
    return bool(destino) and urlsplit(destino).netloc == "" and destino.startswith("/")


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:           # si ya inició sesión, no tiene caso registrarse
        return redirect(url_for("main.panel"))

    form = RegistroForm()
    if form.validate_on_submit():
        # Los que se registran solos reciben el rol "usuario" (los admins los crea otro admin)
        rol_usuario = db.session.scalar(db.select(Rol).filter_by(nombre="usuario"))
        if rol_usuario is None:
            flash("Faltan los roles. Corre en la terminal: flask seed", "danger")
            return render_template("auth/registro.html", form=form)

        usuario = Usuario(nombre=form.nombre.data.strip(), email=form.email.data.lower(),
                          rol=rol_usuario)
        usuario.set_password(form.password.data)   # se guarda el HASH, no la contraseña
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)                          # lo dejamos con la sesión iniciada
        flash(f"¡Bienvenido, {usuario.nombre}! Tu cuenta fue creada.", "success")
        return redirect(url_for("main.panel"))

    return render_template("auth/registro.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.panel"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.scalar(
            db.select(Usuario).filter_by(email=form.email.data.lower())
        )
        # Mismo mensaje si no existe el correo o si la contraseña está mal:
        # así no le decimos a un atacante qué correos sí están registrados.
        if usuario is None or not usuario.check_password(form.password.data):
            flash("Correo o contraseña incorrectos", "danger")
        elif not usuario.activo:
            flash("Tu cuenta está desactivada", "danger")
        else:
            login_user(usuario, remember=form.recordarme.data)
            flash(f"Hola, {usuario.nombre}", "success")

            # Si venía de una página protegida, regresarlo ahí (?next=/panel)
            destino = request.args.get("next")
            return redirect(destino if es_url_segura(destino) else url_for("main.panel"))

    return render_template("auth/login.html", form=form)


@bp.post("/logout")          # POST: cerrar sesión cambia el estado, no debe ser un link GET
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión", "info")
    return redirect(url_for("main.inicio"))
