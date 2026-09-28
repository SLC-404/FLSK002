"""CRUD DE ROLES (protegido por ver/crear/editar/eliminar-roles).

Aquí se ELIGEN los permisos de cada rol (checkboxes). Luego, en Usuarios, a cada usuario
se le asigna un rol. Así:  permisos -> rol -> usuario.
"""
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Permiso, Rol, Usuario
from app.roles import bp
from app.roles.forms import RolForm
from app.utils.decoradores import permiso_requerido

ROLES_PROTEGIDOS = {"admin", "usuario"}   # los usa el sistema: no se borran ni se renombran


def permisos_elegidos(form):
    """Convierte los ids marcados en objetos Permiso."""
    if not form.permisos.data:
        return []
    return db.session.scalars(db.select(Permiso).where(Permiso.id.in_(form.permisos.data))).all()


@bp.get("/")
@login_required
@permiso_requerido("ver-roles")
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
@permiso_requerido("crear-roles")
def nuevo():
    form = RolForm()
    if form.validate_on_submit():
        rol = Rol(nombre=form.nombre.data, descripcion=form.descripcion.data or None)
        rol.permisos = permisos_elegidos(form)      # SQLAlchemy llena rol_permisos solo
        db.session.add(rol)
        db.session.commit()
        flash("Rol creado", "success")
        return redirect(url_for("roles.lista"))
    return render_template("roles/form.html", form=form, titulo="Nuevo rol")


@bp.route("/<int:rol_id>/editar", methods=["GET", "POST"])
@login_required
@permiso_requerido("editar-roles")
def editar(rol_id):
    rol = db.get_or_404(Rol, rol_id)
    form = RolForm(obj=rol, rol_id=rol.id)
    protegido = rol.nombre in ROLES_PROTEGIDOS
    es_admin = rol.nombre == "admin"

    if request.method == "GET":
        # obj=rol no sabe convertir objetos Permiso a ids: se precargan a mano
        form.permisos.data = [p.id for p in rol.permisos]

    if form.validate_on_submit():
        if protegido and form.nombre.data != rol.nombre:
            flash("Este rol lo usa el sistema: no se puede renombrar", "danger")
        else:
            rol.nombre = form.nombre.data
            rol.descripcion = form.descripcion.data or None
            # admin SIEMPRE tiene todos los permisos (para que nadie se quede fuera)
            if es_admin:
                rol.permisos = db.session.scalars(db.select(Permiso)).all()
            else:
                rol.permisos = permisos_elegidos(form)
            db.session.commit()
            flash("Rol actualizado", "success")
            return redirect(url_for("roles.lista"))
    return render_template("roles/form.html", form=form, titulo="Editar rol",
                           protegido=protegido, es_admin=es_admin)


@bp.post("/<int:rol_id>/eliminar")
@login_required
@permiso_requerido("eliminar-roles")
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
