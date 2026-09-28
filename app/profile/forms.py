from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from app.utils.fields import id_document_field, photo_field


class ProfileForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(message="Escribe tu nombre"),
                                             Length(max=80)])
    photo = photo_field()
    id_document = id_document_field()
    submit = SubmitField("Guardar cambios")
