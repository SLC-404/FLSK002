"""USERS CRUD (protected by view/create/edit/delete-users)."""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Role, User
from app.users import bp
from app.users.forms import UserForm
from app.utils.decorators import permission_required
from app.utils.files import delete_file, save_file, was_uploaded


def save_files(form, user):
    """If a photo or ID document was uploaded, save the new one and delete the old one."""
    if was_uploaded(form.photo):
        delete_file(user.photo, "photos")
        user.photo = save_file(form.photo.data, "photos")
    if was_uploaded(form.id_document):
        delete_file(user.id_document, "id_documents")
        user.id_document = save_file(form.id_document.data, "id_documents")
        user.id_document_name = form.id_document.data.filename


@bp.get("/")
@login_required
@permission_required("view-users")
def index():
    q = request.args.get("q", "").strip()
    role_id = request.args.get("role", type=int)

    # joinedload: brings each user's role in the SAME query (avoids N+1)
    stmt = db.select(User).options(joinedload(User.role)).order_by(User.name)
    if q:
        stmt = stmt.where(or_(User.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    if role_id:
        stmt = stmt.where(User.role_id == role_id)

    users = db.session.scalars(stmt).all()
    roles = db.session.scalars(db.select(Role).order_by(Role.name)).all()
    return render_template("users/index.html", users=users, roles=roles, q=q, role_id=role_id)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-users")
def create():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower(),
            role_id=form.role_id.data,      # what was picked in the <select>
            active=form.active.data,        # True/False from the checkbox
        )
        user.set_password(form.password.data)
        save_files(form, user)
        db.session.add(user)
        db.session.commit()
        flash(f"Usuario {user.name} creado", "success")
        return redirect(url_for("users.index"))
    return render_template("users/form.html", form=form, title="Nuevo usuario")


@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-users")
def edit(user_id):
    user = db.get_or_404(User, user_id)
    # obj=user preloads EVERYTHING: name, email, the selected role and the checkbox
    form = UserForm(obj=user, user_id=user.id)
    is_me = user.id == current_user.id

    if form.validate_on_submit():
        # Guards so you can't lock yourself out
        if is_me and not form.active.data:
            flash("No puedes desactivar tu propia cuenta", "danger")
        elif is_me and form.role_id.data != user.role_id:
            flash("No puedes cambiar tu propio rol", "danger")
        else:
            user.name = form.name.data.strip()
            user.email = form.email.data.lower()
            user.role_id = form.role_id.data
            user.active = form.active.data
            if form.password.data:                 # only if a new one was typed
                user.set_password(form.password.data)
            save_files(form, user)
            db.session.commit()
            flash("Usuario actualizado", "success")
            return redirect(url_for("users.index"))

    return render_template("users/form.html", form=form, title="Editar usuario", user=user)


@bp.post("/<int:user_id>/toggle-active")
@login_required
@permission_required("edit-users")
def toggle_active(user_id):
    """Enable/disable with one click from the list."""
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta", "danger")
    else:
        user.active = not user.active
        db.session.commit()
        status = "activado" if user.active else "desactivado"
        flash(f"{user.name} {status}", "info")
    return redirect(request.referrer or url_for("users.index"))


@bp.post("/<int:user_id>/delete")
@login_required
@permission_required("delete-users")
def delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta", "danger")
        return redirect(url_for("users.index"))

    name = user.name
    delete_file(user.photo, "photos")
    delete_file(user.id_document, "id_documents")
    db.session.delete(user)
    db.session.commit()
    flash(f"Usuario {name} eliminado", "warning")
    return redirect(url_for("users.index"))
