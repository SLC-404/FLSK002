from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from app.utils.campos import campo_foto, campo_identificacion


class PerfilForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(message="Escribe tu nombre"),
                                               Length(max=80)])
    foto = campo_foto()
    identificacion = campo_identificacion()
    enviar = SubmitField("Guardar cambios")
