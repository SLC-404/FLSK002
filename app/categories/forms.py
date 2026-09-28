from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.extensions import db
from app.models import Category


class CategoryForm(FlaskForm):
    name = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre de la categoría"),
        Length(max=100),
    ])
    description = StringField("Descripción", validators=[Optional(), Length(max=250)])
    submit = SubmitField("Guardar")

    def __init__(self, *args, category_id=None, **kwargs):
        """category_id: when EDITING, so it doesn't clash with itself in the unique check."""
        super().__init__(*args, **kwargs)
        self.category_id = category_id

    def validate_name(self, field):
        stmt = db.select(Category).where(Category.name == field.data.strip())
        if self.category_id is not None:
            stmt = stmt.where(Category.id != self.category_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe una categoría con ese nombre")
