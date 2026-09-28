from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app.extensions import db
from app.models import Permission


class PermissionForm(FlaskForm):
    name = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre del permiso"),
        Length(max=50),
        Regexp(r"^[a-z]+-[a-z_]+$", message="Formato accion-modulo en minúsculas (ej. view-products)"),
    ])
    description = StringField("Descripción", validators=[Optional(), Length(max=150)])
    submit = SubmitField("Guardar")

    def __init__(self, *args, permission_id=None, **kwargs):
        """permission_id: when EDITING, so it doesn't clash with itself in the unique check."""
        super().__init__(*args, **kwargs)
        self.permission_id = permission_id

    def validate_name(self, field):
        stmt = db.select(Permission).where(Permission.name == field.data)
        if self.permission_id is not None:
            stmt = stmt.where(Permission.id != self.permission_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un permiso con ese nombre")
