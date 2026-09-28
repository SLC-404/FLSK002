from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app.extensions import db
from app.models import Permiso


class PermisoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre del permiso"),
        Length(max=50),
        Regexp(r"^[a-z]+-[a-z_]+$", message="Formato accion-modulo en minúsculas (ej. ver-productos)"),
    ])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=150)])
    enviar = SubmitField("Guardar")

    def __init__(self, *args, permiso_id=None, **kwargs):
        """permiso_id: al EDITAR, para no chocar consigo mismo en la validación de único."""
        super().__init__(*args, **kwargs)
        self.permiso_id = permiso_id

    def validate_nombre(self, campo):
        stmt = db.select(Permiso).where(Permiso.nombre == campo.data)
        if self.permiso_id is not None:
            stmt = stmt.where(Permiso.id != self.permiso_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un permiso con ese nombre")
