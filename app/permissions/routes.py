"""PERMISSIONS CRUD (protected by view/create/edit/delete-permissions)."""
from flask import flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Permission, role_permissions
from app.permissions import bp
from app.permissions.catalog import BASE_PERMISSIONS
from app.permissions.forms import PermissionForm
from app.utils.decorators import permission_required


@bp.get("/")
@login_required
@permission_required("view-permissions")
def index():
    # Each permission with how many roles have it (LEFT JOIN to the pivot table + COUNT)
    stmt = (
        db.select(Permission, func.count(role_permissions.c.role_id).label("total"))
        .outerjoin(role_permissions, role_permissions.c.permission_id == Permission.id)
        .group_by(Permission.id)
        .order_by(Permission.name)
    )
    rows = db.session.execute(stmt).all()
    return render_template("permissions/index.html", rows=rows, system=BASE_PERMISSIONS)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-permissions")
def create():
    form = PermissionForm()
    if form.validate_on_submit():
        db.session.add(Permission(name=form.name.data, description=form.description.data or None))
        db.session.commit()
        flash("Permiso creado. Ahora asígnalo a un rol en Roles → Editar.", "success")
        return redirect(url_for("permissions.index"))
    return render_template("permissions/form.html", form=form, title="Nuevo permiso")


@bp.route("/<int:permission_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-permissions")
def edit(permission_id):
    permission = db.get_or_404(Permission, permission_id)
    form = PermissionForm(obj=permission, permission_id=permission.id)
    protected = permission.name in BASE_PERMISSIONS

    if form.validate_on_submit():
        if protected and form.name.data != permission.name:
            flash("Este permiso lo usa el sistema: no se puede renombrar", "danger")
        else:
            permission.name = form.name.data
            permission.description = form.description.data or None
            db.session.commit()
            flash("Permiso actualizado", "success")
            return redirect(url_for("permissions.index"))
    return render_template("permissions/form.html", form=form, title="Editar permiso",
                           protected=protected)


@bp.post("/<int:permission_id>/delete")
@login_required
@permission_required("delete-permissions")
def delete(permission_id):
    permission = db.get_or_404(Permission, permission_id)
    if permission.name in BASE_PERMISSIONS:
        flash("Este permiso lo usa el sistema: no se puede eliminar", "danger")
    else:
        name = permission.name
        db.session.delete(permission)     # SQLAlchemy removes its role_permissions rows
        db.session.commit()
        flash(f"Permiso '{name}' eliminado", "warning")
    return redirect(url_for("permissions.index"))
