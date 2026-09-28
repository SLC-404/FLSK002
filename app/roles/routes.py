"""ROLES CRUD (protected by view/create/edit/delete-roles).

This is where each role's permissions are CHOSEN (checkboxes). Then, in Users, each user
gets a role. So:  permissions -> role -> user.
"""
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Permission, Role, User
from app.roles import bp
from app.roles.forms import RoleForm
from app.utils.decorators import permission_required

PROTECTED_ROLES = {"admin", "user"}   # used by the system: can't be deleted or renamed


def selected_permissions(form):
    """Turns the checked ids into Permission objects."""
    if not form.permissions.data:
        return []
    return db.session.scalars(
        db.select(Permission).where(Permission.id.in_(form.permissions.data))).all()


@bp.get("/")
@login_required
@permission_required("view-roles")
def index():
    # Each role with how many users it has (LEFT JOIN + COUNT + GROUP BY)
    stmt = (
        db.select(Role, func.count(User.id).label("total"))
        .outerjoin(Role.users)
        .group_by(Role.id)
        .order_by(Role.name)
    )
    rows = db.session.execute(stmt).all()      # several things per row -> execute
    return render_template("roles/index.html", rows=rows, protected=PROTECTED_ROLES)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-roles")
def create():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data, description=form.description.data or None)
        role.permissions = selected_permissions(form)   # SQLAlchemy fills role_permissions
        db.session.add(role)
        db.session.commit()
        flash("Rol creado", "success")
        return redirect(url_for("roles.index"))
    return render_template("roles/form.html", form=form, title="Nuevo rol")


@bp.route("/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-roles")
def edit(role_id):
    role = db.get_or_404(Role, role_id)
    form = RoleForm(obj=role, role_id=role.id)
    protected = role.name in PROTECTED_ROLES
    is_admin = role.name == "admin"

    if request.method == "GET":
        # obj=role can't turn Permission objects into ids: preload them by hand
        form.permissions.data = [p.id for p in role.permissions]

    if form.validate_on_submit():
        if protected and form.name.data != role.name:
            flash("Este rol lo usa el sistema: no se puede renombrar", "danger")
        else:
            role.name = form.name.data
            role.description = form.description.data or None
            # admin ALWAYS has every permission (so nobody gets locked out)
            if is_admin:
                role.permissions = db.session.scalars(db.select(Permission)).all()
            else:
                role.permissions = selected_permissions(form)
            db.session.commit()
            flash("Rol actualizado", "success")
            return redirect(url_for("roles.index"))
    return render_template("roles/form.html", form=form, title="Editar rol",
                           protected=protected, is_admin=is_admin)


@bp.post("/<int:role_id>/delete")
@login_required
@permission_required("delete-roles")
def delete(role_id):
    role = db.get_or_404(Role, role_id)
    if role.name in PROTECTED_ROLES:
        flash("Este rol lo usa el sistema: no se puede eliminar", "danger")
    elif role.users:
        flash(f"No se puede eliminar: {len(role.users)} usuario(s) tienen este rol", "danger")
    else:
        name = role.name            # save it BEFORE: after the commit the object is gone
        db.session.delete(role)
        db.session.commit()
        flash(f"Rol '{name}' eliminado", "warning")
    return redirect(url_for("roles.index"))
