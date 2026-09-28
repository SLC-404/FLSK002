"""CRUD DE USUARIOS (solo admin)."""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Rol, Usuario
from app.usuarios import bp
from app.usuarios.forms import UsuarioForm
from app.utils.archivos import borrar_archivo, guardar_archivo, se_subio
from app.utils.decoradores import rol_requerido


def guardar_archivos(form, usuario):
    """Si subieron foto o identificación, guarda las nuevas y borra las anteriores."""
    if se_subio(form.foto):
        borrar_archivo(usuario.foto, "fotos")
        usuario.foto = guardar_archivo(form.foto.data, "fotos")
    if se_subio(form.identificacion):
        borrar_archivo(usuario.identificacion, "identificaciones")
        usuario.identificacion = guardar_archivo(form.identificacion.data, "identificaciones")
        usuario.identificacion_nombre = form.identificacion.data.filename


@bp.get("/")
@login_required
@rol_requerido("admin")
def lista():
    q = request.args.get("q", "").strip()
    rol_id = request.args.get("rol", type=int)

    # joinedload: trae el rol de cada usuario en la MISMA consulta (evita el N+1)
    stmt = db.select(Usuario).options(joinedload(Usuario.rol)).order_by(Usuario.nombre)
    if q:
        stmt = stmt.where(or_(Usuario.nombre.ilike(f"%{q}%"), Usuario.email.ilike(f"%{q}%")))
    if rol_id:
        stmt = stmt.where(Usuario.rol_id == rol_id)

    usuarios = db.session.scalars(stmt).all()
    roles = db.session.scalars(db.select(Rol).order_by(Rol.nombre)).all()
    return render_template("usuarios/lista.html", usuarios=usuarios, roles=roles,
                           q=q, rol_id=rol_id)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def nuevo():
    form = UsuarioForm()
    if form.validate_on_submit():
        usuario = Usuario(
            nombre=form.nombre.data.strip(),
            email=form.email.data.lower(),
            rol_id=form.rol_id.data,      # ← lo que eligió en el <select>
            activo=form.activo.data,      # ← True/False del checkbox
        )
        usuario.set_password(form.password.data)
        guardar_archivos(form, usuario)
        db.session.add(usuario)
        db.session.commit()
        flash(f"Usuario {usuario.nombre} creado", "success")
        return redirect(url_for("usuarios.lista"))
    return render_template("usuarios/form.html", form=form, titulo="Nuevo usuario")


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def editar(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    # obj=usuario precarga TODO: nombre, email, el rol seleccionado en el select y el checkbox
    form = UsuarioForm(obj=usuario, usuario_id=usuario.id)
    es_yo = usuario.id == current_user.id

    if form.validate_on_submit():
        rol_nuevo = db.session.get(Rol, form.rol_id.data)
        # Candados para no dejarte fuera a ti mismo
        if es_yo and not form.activo.data:
            flash("No puedes desactivar tu propia cuenta", "danger")
        elif es_yo and rol_nuevo.nombre != "admin":
            flash("No puedes quitarte el rol de admin a ti mismo", "danger")
        else:
            usuario.nombre = form.nombre.data.strip()
            usuario.email = form.email.data.lower()
            usuario.rol_id = form.rol_id.data
            usuario.activo = form.activo.data
            if form.password.data:                 # solo si escribieron una nueva
                usuario.set_password(form.password.data)
            guardar_archivos(form, usuario)
            db.session.commit()
            flash("Usuario actualizado", "success")
            return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/form.html", form=form, titulo="Editar usuario",
                           usuario=usuario)


@bp.post("/<int:usuario_id>/activo")
@login_required
@rol_requerido("admin")
def cambiar_activo(usuario_id):
    """Activa/desactiva con un clic desde la lista."""
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta", "danger")
    else:
        usuario.activo = not usuario.activo
        db.session.commit()
        estado = "activado" if usuario.activo else "desactivado"
        flash(f"{usuario.nombre} {estado}", "info")
    return redirect(request.referrer or url_for("usuarios.lista"))


@bp.post("/<int:usuario_id>/eliminar")
@login_required
@rol_requerido("admin")
def eliminar(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta", "danger")
        return redirect(url_for("usuarios.lista"))

    nombre = usuario.nombre
    borrar_archivo(usuario.foto, "fotos")
    borrar_archivo(usuario.identificacion, "identificaciones")
    db.session.delete(usuario)
    db.session.commit()
    flash(f"Usuario {nombre} eliminado", "warning")
    return redirect(url_for("usuarios.lista"))
