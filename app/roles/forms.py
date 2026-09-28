from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget

from app.extensions import db
from app.models import Permission, Role


class CheckboxListField(SelectMultipleField):
    """A SelectMultipleField rendered as CHECKBOXES instead of a <select multiple>."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class RoleForm(FlaskForm):
    name = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre del rol"),
        Length(max=30),
        Regexp(r"^[a-z_]+$", message="Solo minúsculas y guion bajo (ej. supervisor)"),
    ])
    description = StringField("Descripción", validators=[Optional(), Length(max=150)])
    # List of checked permission ids -> [1, 4, 7]
    permissions = CheckboxListField("Permisos", coerce=int)
    submit = SubmitField("Guardar")

    def __init__(self, *args, role_id=None, **kwargs):
        """role_id: when EDITING, so it doesn't clash with itself in the unique check."""
        super().__init__(*args, **kwargs)
        self.role_id = role_id
        # Options come from the DB, sorted by module and then by name
        permissions = db.session.scalars(db.select(Permission)).all()
        permissions.sort(key=lambda p: (p.module, p.name))
        self.permissions.choices = [(p.id, p.name) for p in permissions]

    def validate_name(self, field):
        stmt = db.select(Role).where(Role.name == field.data)
        if self.role_id is not None:
            stmt = stmt.where(Role.id != self.role_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un rol con ese nombre")
