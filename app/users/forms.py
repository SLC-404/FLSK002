"""USER FORM (filled by someone with create/edit-users).

  - role_id -> SelectField   (a <select> with the roles from the DB)
  - active  -> BooleanField  (a checkbox: checked = active)
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from app.extensions import db
from app.models import Role, User
from app.utils.fields import id_document_field, photo_field


class UserForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(message="Escribe el nombre"),
                                             Length(max=80)])
    email = EmailField("Correo", validators=[DataRequired(message="Escribe el correo"),
                                             Email(message="Correo no válido"), Length(max=120)])

    # SELECT: coerce=int turns the <option> value ("2") into a number (2) = role_id
    role_id = SelectField("Rol", coerce=int)

    # CHECKBOX: True if checked, False if not
    active = BooleanField("Usuario activo", default=True)

    # Password: required when CREATING, optional when EDITING (set in __init__)
    password = PasswordField("Contraseña", validators=[
        Optional(), Length(min=8, message="Mínimo 8 caracteres")])
    confirm = PasswordField("Confirmar contraseña", validators=[
        EqualTo("password", message="Las contraseñas no coinciden")])

    photo = photo_field()
    id_document = id_document_field()
    submit = SubmitField("Guardar")

    def __init__(self, *args, user_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id   # None = creating, a number = editing

        # <select> options come from the DB: [(1, "admin"), (2, "user"), ...]
        roles = db.session.scalars(db.select(Role).order_by(Role.name)).all()
        self.role_id.choices = [(r.id, r.name) for r in roles]

        if user_id is None:
            self.password.validators = [DataRequired(message="Escribe una contraseña"),
                                        Length(min=8, message="Mínimo 8 caracteres")]

    def validate_email(self, field):
        stmt = db.select(User).where(User.email == field.data.lower())
        if self.user_id is not None:
            stmt = stmt.where(User.id != self.user_id)   # when editing, ignore yourself
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe un usuario con ese correo")
