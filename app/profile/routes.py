"""USER PROFILE + SERVING PRIVATE FILES."""
from flask import abort, flash, redirect, render_template, send_from_directory, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User
from app.profile import bp
from app.profile.forms import ProfileForm
from app.utils.files import delete_file, folder, save_file, was_uploaded


@bp.route("/", methods=["GET", "POST"])
@login_required
def show():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()

        # was_uploaded(): did they pick a new file? (if not, the old one stays)
        if was_uploaded(form.photo):
            delete_file(current_user.photo, "photos")                    # remove the old one
            current_user.photo = save_file(form.photo.data, "photos")    # DB stores the name

        if was_uploaded(form.id_document):
            delete_file(current_user.id_document, "id_documents")
            current_user.id_document = save_file(form.id_document.data, "id_documents")
            current_user.id_document_name = form.id_document.data.filename

        db.session.commit()
        flash("Perfil actualizado", "success")
        return redirect(url_for("profile.show"))    # PRG

    return render_template("profile/show.html", form=form)


@bp.get("/<int:user_id>/photo")
@login_required
def photo(user_id):
    """Serves the profile photo (any logged-in user can see it)."""
    user = db.get_or_404(User, user_id)
    if not user.photo:
        abort(404)
    return send_from_directory(folder("photos"), user.photo)


@bp.get("/<int:user_id>/id-document")
@login_required
def id_document(user_id):
    """Serves the ID document: ONLY the owner or someone with "view-users" (private file)."""
    user = db.get_or_404(User, user_id)
    if current_user.id != user.id and not current_user.can("view-users"):
        abort(403)
    if not user.id_document:
        abort(404)
    return send_from_directory(folder("id_documents"), user.id_document,
                               download_name=user.id_document_name)
