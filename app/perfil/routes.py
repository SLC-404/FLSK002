"""PERFIL DEL USUARIO + SERVIR ARCHIVOS PRIVADOS."""
from flask import abort, flash, redirect, render_template, send_from_directory, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Usuario
from app.perfil import bp
from app.perfil.forms import PerfilForm
from app.utils.archivos import borrar_archivo, carpeta, guardar_archivo, se_subio


@bp.route("/", methods=["GET", "POST"])
@login_required
def ver():
    form = PerfilForm(obj=current_user)

    if form.validate_on_submit():
        current_user.nombre = form.nombre.data.strip()

        # se_subio(): ¿eligieron un archivo nuevo? (si no, se queda el anterior)
        if se_subio(form.foto):
            borrar_archivo(current_user.foto, "fotos")                     # adiós a la anterior
            current_user.foto = guardar_archivo(form.foto.data, "fotos")   # en la BD: el nombre

        if se_subio(form.identificacion):
            borrar_archivo(current_user.identificacion, "identificaciones")
            current_user.identificacion = guardar_archivo(form.identificacion.data,
                                                          "identificaciones")
            current_user.identificacion_nombre = form.identificacion.data.filename

        db.session.commit()
        flash("Perfil actualizado", "success")
        return redirect(url_for("perfil.ver"))    # PRG

    return render_template("perfil/ver.html", form=form)


@bp.get("/<int:usuario_id>/foto")
@login_required
def foto(usuario_id):
    """Sirve la foto de perfil (cualquier usuario con sesión puede verla)."""
    usuario = db.get_or_404(Usuario, usuario_id)
    if not usuario.foto:
        abort(404)
    return send_from_directory(carpeta("fotos"), usuario.foto)


@bp.get("/<int:usuario_id>/identificacion")
@login_required
def identificacion(usuario_id):
    """Sirve la identificación: SOLO el dueño o un admin (es un documento privado)."""
    usuario = db.get_or_404(Usuario, usuario_id)
    if current_user.id != usuario.id and not current_user.es_admin:
        abort(403)
    if not usuario.identificacion:
        abort(404)
    return send_from_directory(carpeta("identificaciones"), usuario.identificacion,
                               download_name=usuario.identificacion_nombre)
