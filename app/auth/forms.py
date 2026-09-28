"""FORMULARIOS DE AUTENTICACIÓN (mismo principio que el capítulo 6)."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.extensions import db
from app.models import Usuario


class LoginForm(FlaskForm):
    email = EmailField("Correo", validators=[
        DataRequired(message="Escribe tu correo"),
        Email(message="Correo no válido"),
    ])
    password = PasswordField("Contraseña", validators=[
        DataRequired(message="Escribe tu contraseña"),
    ])
    recordarme = BooleanField("Recordarme")
    enviar = SubmitField("Entrar")


class RegistroForm(FlaskForm):
    nombre = StringField("Nombre", validators=[
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
    confirmar = PasswordField("Confirmar contraseña", validators=[
        DataRequired(message="Confirma tu contraseña"),
        EqualTo("password", message="Las contraseñas no coinciden"),   # = 'confirmed' en Laravel
    ])
    enviar = SubmitField("Crear cuenta")

    def validate_email(self, campo):
        """Validación PERSONALIZADA: WTForms llama solo a los métodos validate_<campo>.
        Aquí revisamos en la BD que el correo no esté registrado (como 'unique:usuarios')."""
        existe = db.session.scalar(
            db.select(Usuario).filter_by(email=campo.data.lower())
        )
        if existe:
            raise ValidationError("Ya existe una cuenta con ese correo")
