from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional

from app.extensions import db
from app.models import Category


class ProductForm(FlaskForm):
    name = StringField("Nombre", validators=[
        DataRequired(message="Escribe el nombre del producto"), Length(max=100)])
    description = StringField("Descripción", validators=[Optional(), Length(max=250)])
    # DecimalField -> Decimal("15000.00"); places=2 = 2 decimals
    price = DecimalField("Precio", places=2, validators=[
        InputRequired(message="Escribe el precio"),
        NumberRange(min=0, message="El precio no puede ser negativo")])
    # InputRequired (not DataRequired) so that 0 is accepted as a valid stock
    stock = IntegerField("Stock", default=0, validators=[
        InputRequired(message="Escribe el stock"),
        NumberRange(min=0, message="El stock no puede ser negativo")])
    # SELECT with the categories from the DB; coerce=int -> "2" becomes 2
    category_id = SelectField("Categoría", coerce=int)
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
        self.category_id.choices = [(c.id, c.name) for c in categories]
