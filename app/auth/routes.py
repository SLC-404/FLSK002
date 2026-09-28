"""AUTH ROUTES

Flask-Login gives us:
  login_user(user)   -> starts the session   (Auth::login)
  logout_user()      -> ends the session     (Auth::logout)
  current_user       -> the current user     (Auth::user)
  @login_required    -> protects a route     (middleware 'auth')
"""
from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm
from app.extensions import db
from app.models import Role, User


def is_safe_url(target):
    """Only allow redirects to routes of OUR app (starting with /).
    Prevents links like /auth/login?next=https://evil-site.com"""
    return bool(target) and urlsplit(target).netloc == "" and target.startswith("/")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Self-registered users get the "user" role (admins are created by another admin)
        user_role = db.session.scalar(db.select(Role).filter_by(name="user"))
        if user_role is None:
            flash("Faltan los roles. Corre en la terminal: flask seed", "danger")
            return render_template("auth/register.html", form=form)

        user = User(name=form.name.data.strip(), email=form.email.data.lower(), role=user_role)
        user.set_password(form.password.data)   # stores the HASH, not the password
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"¡Bienvenido, {user.name}! Tu cuenta fue creada.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).filter_by(email=form.email.data.lower()))
        # Same message for unknown email or wrong password:
        # we don't tell an attacker which emails are registered.
        if user is None or not user.check_password(form.password.data):
            flash("Correo o contraseña incorrectos", "danger")
        elif not user.active:
            flash("Tu cuenta está desactivada", "danger")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Hola, {user.name}", "success")

            # If they came from a protected page, send them back (?next=/dashboard)
            target = request.args.get("next")
            return redirect(target if is_safe_url(target) else url_for("main.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.post("/logout")          # POST: logging out changes state, it shouldn't be a GET link
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión", "info")
    return redirect(url_for("main.index"))
