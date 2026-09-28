"""FORMULARIO DE USUARIO (lo llena un admin).

Aquí están los dos campos que pediste:
  - rol    -> SelectField   (un <select> con los roles de la BD)
  - activo -> BooleanField  (un checkbox: marcado = activo)
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from app.extensions import db
from app.models import Rol, Usuario
from app.utils.campos import campo_foto, campo_identificacion


class UsuarioForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(message="Escribe el nombre"),
                                               Length(max=80)])
    email = EmailField("Correo", validators=[DataRequired(message="Escribe el correo"),
                                             Email(message="Correo no válido"), Length(max=120)])

    # SELECT: coerce=int convierte el value del <option> ("2") en número (2) = rol_id
    rol_id = SelectField("Rol", coerce=int)

    # CHECKBOX: True si está marcado, False si no
    activo = BooleanField("Usuario activo", default=True)

    # Contraseña: obligatoria al CREAR, opcional al EDITAR (se revisa en __init__)
    password = PasswordField("Contraseña", validators=[
        Optional(), Length(min=8, message="Mínimo 8 caracteres")])
    confirmar = PasswordField("Confirmar contraseña", validators=[
        EqualTo("password", message="Las contraseñas no coinciden")])

    foto = campo_foto()
    identificacion = campo_identificacion()
    enviar = SubmitField("Guardar")

    def __init__(self, *args, usuario_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_id = usuario_id   # None = creando, un número = editando

        # Las opciones del <select> salen de la BD: [(1, "admin"), (2, "usuario"), ...]
        roles = db.session.scalars(db.select(Rol).order_by(Rol.nombre)).all()
        self.rol_id.choices = [(r.id, r.nombre) for r in roles]

        # Al crear, la contraseña es obligatoria
        if usuario_id is None:
            self.password.validators = [DataRequired(message="Escribe una contraseña"),
                                        Length(min=8, message="Mínimo 8 caracteres")]

    def validate_email(self, campo):
        stmt = db.select(Usuario).where(Usuario.email == campo.data.lower())
        if self.usuario_id is not None:
            stmt = stmt.where(Usuario.id != self.usuario_id)   # al editar, no contarse a sí mismo
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un usuario con ese correo")
