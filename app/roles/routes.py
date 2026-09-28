"""CRUD DE ROLES (solo admin)."""
from flask import flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Rol, Usuario
from app.roles import bp
from app.roles.forms import RolForm
from app.utils.decoradores import rol_requerido

ROLES_PROTEGIDOS = {"admin", "usuario"}   # los usa el sistema: no se borran ni se renombran


@bp.get("/")
@login_required
@rol_requerido("admin")
def lista():
    # Cada rol con cuántos usuarios tiene (LEFT JOIN + COUNT + GROUP BY)
    stmt = (
        db.select(Rol, func.count(Usuario.id).label("total"))
        .outerjoin(Rol.usuarios)
        .group_by(Rol.id)
        .order_by(Rol.nombre)
    )
    filas = db.session.execute(stmt).all()      # varias cosas por fila -> execute
    return render_template("roles/lista.html", filas=filas, protegidos=ROLES_PROTEGIDOS)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def nuevo():
    form = RolForm()
    if form.validate_on_submit():
        db.session.add(Rol(nombre=form.nombre.data, descripcion=form.descripcion.data or None))
        db.session.commit()
        flash("Rol creado", "success")
        return redirect(url_for("roles.lista"))
    return render_template("roles/form.html", form=form, titulo="Nuevo rol")


@bp.route("/<int:rol_id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def editar(rol_id):
    rol = db.get_or_404(Rol, rol_id)
    form = RolForm(obj=rol, rol_id=rol.id)
    protegido = rol.nombre in ROLES_PROTEGIDOS

    if form.validate_on_submit():
        if protegido and form.nombre.data != rol.nombre:
            flash("Este rol lo usa el sistema: no se puede renombrar", "danger")
        else:
            rol.nombre = form.nombre.data
            rol.descripcion = form.descripcion.data or None
            db.session.commit()
            flash("Rol actualizado", "success")
            return redirect(url_for("roles.lista"))
    return render_template("roles/form.html", form=form, titulo="Editar rol", protegido=protegido)


@bp.post("/<int:rol_id>/eliminar")
@login_required
@rol_requerido("admin")
def eliminar(rol_id):
    rol = db.get_or_404(Rol, rol_id)
    if rol.nombre in ROLES_PROTEGIDOS:
        flash("Este rol lo usa el sistema: no se puede eliminar", "danger")
    elif rol.usuarios:
        flash(f"No se puede eliminar: {len(rol.usuarios)} usuario(s) tienen este rol", "danger")
    else:
        nombre = rol.nombre            # guardarlo ANTES: después del commit el objeto ya no existe
        db.session.delete(rol)
        db.session.commit()
        flash(f"Rol '{nombre}' eliminado", "warning")
    return redirect(url_for("roles.lista"))
