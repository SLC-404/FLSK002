"""AUTH FORMS."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.extensions import db
from app.models import User


class LoginForm(FlaskForm):
    email = EmailField("Correo", validators=[
        DataRequired(message="Escribe tu correo"),
        Email(message="Correo no válido"),
    ])
    password = PasswordField("Contraseña", validators=[
        DataRequired(message="Escribe tu contraseña"),
    ])
    remember = BooleanField("Recordarme")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    name = StringField("Nombre", validators=[
        DataRequired(message="Escribe tu nombre"),
        Length(max=80),
    ])
    email = EmailField("Correo", validators=[
        DataRequired(message="Escribe tu correo"),
        Email(message="Correo no válido"),
        Length(max=120),
    ])
    password = PasswordField("Contraseña", validators=[
        DataRequired(message="Escribe una contraseña"),
        Length(min=8, message="Mínimo 8 caracteres"),
    ])
    confirm = PasswordField("Confirmar contraseña", validators=[
        DataRequired(message="Confirma tu contraseña"),
        EqualTo("password", message="Las contraseñas no coinciden"),   # = 'confirmed' in Laravel
    ])
    submit = SubmitField("Crear cuenta")

    def validate_email(self, field):
        """CUSTOM validation: WTForms automatically calls every validate_<field> method.
        Checks the email is not registered yet (like 'unique:users' in Laravel)."""
        exists = db.session.scalar(db.select(User).filter_by(email=field.data.lower()))
        if exists:
            raise ValidationError("Ya existe una cuenta con ese correo")
