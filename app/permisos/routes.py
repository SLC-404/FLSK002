"""CRUD DE PERMISOS (protegido por ver/crear/editar/eliminar-permisos)."""
from flask import flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Permiso, rol_permisos
from app.permisos import bp
from app.permisos.catalogo import PERMISOS_BASE
from app.permisos.forms import PermisoForm
from app.utils.decoradores import permiso_requerido


@bp.get("/")
@login_required
@permiso_requerido("ver-permisos")
def lista():
    # Cada permiso con en cuántos roles está (LEFT JOIN a la tabla intermedia + COUNT)
    stmt = (
        db.select(Permiso, func.count(rol_permisos.c.rol_id).label("total"))
        .outerjoin(rol_permisos, rol_permisos.c.permiso_id == Permiso.id)
        .group_by(Permiso.id)
        .order_by(Permiso.nombre)
    )
    filas = db.session.execute(stmt).all()
    return render_template("permisos/lista.html", filas=filas, sistema=PERMISOS_BASE)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@permiso_requerido("crear-permisos")
def nuevo():
    form = PermisoForm()
    if form.validate_on_submit():
        db.session.add(Permiso(nombre=form.nombre.data, descripcion=form.descripcion.data or None))
        db.session.commit()
        flash("Permiso creado. Ahora asígnalo a un rol en Roles → Editar.", "success")
        return redirect(url_for("permisos.lista"))
    return render_template("permisos/form.html", form=form, titulo="Nuevo permiso")


@bp.route("/<int:permiso_id>/editar", methods=["GET", "POST"])
@login_required
@permiso_requerido("editar-permisos")
def editar(permiso_id):
    permiso = db.get_or_404(Permiso, permiso_id)
    form = PermisoForm(obj=permiso, permiso_id=permiso.id)
    protegido = permiso.nombre in PERMISOS_BASE

    if form.validate_on_submit():
        if protegido and form.nombre.data != permiso.nombre:
            flash("Este permiso lo usa el sistema: no se puede renombrar", "danger")
        else:
            permiso.nombre = form.nombre.data
            permiso.descripcion = form.descripcion.data or None
            db.session.commit()
            flash("Permiso actualizado", "success")
            return redirect(url_for("permisos.lista"))
    return render_template("permisos/form.html", form=form, titulo="Editar permiso",
                           protegido=protegido)


@bp.post("/<int:permiso_id>/eliminar")
@login_required
@permiso_requerido("eliminar-permisos")
def eliminar(permiso_id):
    permiso = db.get_or_404(Permiso, permiso_id)
    if permiso.nombre in PERMISOS_BASE:
        flash("Este permiso lo usa el sistema: no se puede eliminar", "danger")
    else:
        nombre = permiso.nombre
        db.session.delete(permiso)     # SQLAlchemy borra solo sus filas en rol_permisos
        db.session.commit()
        flash(f"Permiso '{nombre}' eliminado", "warning")
    return redirect(url_for("permisos.lista"))
