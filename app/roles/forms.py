from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app.extensions import db
from app.models import Permiso, Rol


class CasillasField(SelectMultipleField):
    """Un SelectMultipleField que se dibuja como CHECKBOXES en lugar de <select multiple>."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class RolForm(FlaskForm):
    nombre = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre del rol"),
        Length(max=30),
        Regexp(r"^[a-z_]+$", message="Solo minúsculas y guion bajo (ej. supervisor)"),
    ])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=150)])
    # Lista de ids de permisos marcados -> [1, 4, 7]
    permisos = CasillasField("Permisos", coerce=int)
    enviar = SubmitField("Guardar")

    def __init__(self, *args, rol_id=None, **kwargs):
        """rol_id: al EDITAR, para no chocar consigo mismo en la validación de único."""
        super().__init__(*args, **kwargs)
        self.rol_id = rol_id
        # Las opciones salen de la BD, ordenadas por módulo y luego por nombre
        permisos = db.session.scalars(db.select(Permiso)).all()
        permisos.sort(key=lambda p: (p.modulo, p.nombre))
        self.permisos.choices = [(p.id, p.nombre) for p in permisos]

    def validate_nombre(self, campo):
        stmt = db.select(Rol).where(Rol.nombre == campo.data)
        if self.rol_id is not None:
            stmt = stmt.where(Rol.id != self.rol_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un rol con ese nombre")
