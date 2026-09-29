"""REST API: categories and products.

  GET    /api/categories              list
  POST   /api/categories              create      body: {"name": "...", "description": "..."}
  GET    /api/categories/<id>         one
  PUT    /api/categories/<id>         update
  DELETE /api/categories/<id>         delete

  GET    /api/products?q=&category=&in_stock=1&page=1&per_page=10
  POST   /api/products                body: {"name", "price", "stock", "category_id", "description"}
  GET    /api/products/<id>
  PUT    /api/products/<id>           (partial: only the fields you send)
  DELETE /api/products/<id>

Test from the terminal:
  curl http://127.0.0.1:5000/api/products
  curl -X POST http://127.0.0.1:5000/api/products -H "Content-Type: application/json" \\
       -H "X-API-Key: <API_KEY>" -d '{"name":"Mouse","price":350,"stock":10,"category_id":1}'
"""
from decimal import Decimal, InvalidOperation

from flask import jsonify, request
from sqlalchemy.orm import joinedload

from app.api import bp
from app.extensions import db
from app.models import Category, Product
from app.utils.decorators import api_key_required


# ---------------------------------------------------------------- helpers
def get_json():
    """Request body as dict. silent=True -> None instead of an error if it's not JSON."""
    return request.get_json(silent=True) or {}


def validate_product(data, partial=False):
    """Validates the JSON by hand. Returns (clean_data, errors).
    partial=True (PUT) -> only checks the fields that came."""
    clean, errors = {}, {}

    if "name" in data or not partial:
        name = str(data.get("name") or "").strip()
        if not name:
            errors["name"] = "Es obligatorio"
        elif len(name) > 100:
            errors["name"] = "Máximo 100 caracteres"
        clean["name"] = name

    if "description" in data:
        clean["description"] = (str(data["description"]).strip() or None) if data["description"] else None

    if "price" in data or not partial:
        try:
            price = Decimal(str(data.get("price")))
            if price < 0:
                errors["price"] = "No puede ser negativo"
            clean["price"] = price
        except (InvalidOperation, ValueError):
            errors["price"] = "Debe ser un número"

    if "stock" in data or not partial:
        stock = data.get("stock", 0)
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            errors["stock"] = "Debe ser un entero mayor o igual a 0"
        clean["stock"] = stock

    if "category_id" in data or not partial:
        if not db.session.get(Category, data.get("category_id") or 0):
            errors["category_id"] = "La categoría no existe"
        clean["category_id"] = data.get("category_id")

    return clean, errors


# ---------------------------------------------------------------- categories
@bp.get("/categories")
@api_key_required
def categories_index():
    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return jsonify([c.to_dict() for c in categories])


@bp.get("/categories/<int:category_id>")
@api_key_required
def categories_show(category_id):
    return jsonify(db.get_or_404(Category, category_id).to_dict())


@bp.post("/categories")
@api_key_required
def categories_create():
    data = get_json()
    name = str(data.get("name") or "").strip()
    if not name:
        return jsonify(errors={"name": "Es obligatorio"}), 422
    if db.session.scalar(db.select(Category).filter_by(name=name)):
        return jsonify(errors={"name": "Ya existe"}), 422
    category = Category(name=name, description=data.get("description") or None)
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201            # 201 = Created


@bp.put("/categories/<int:category_id>")
@api_key_required
def categories_update(category_id):
    category = db.get_or_404(Category, category_id)
    data = get_json()
    if "name" in data:
        name = str(data["name"] or "").strip()
        exists = db.session.scalar(
            db.select(Category).where(Category.name == name, Category.id != category.id))
        if not name or exists:
            return jsonify(errors={"name": "Obligatorio y único"}), 422
        category.name = name
    if "description" in data:
        category.description = data["description"] or None
    db.session.commit()
    return jsonify(category.to_dict())


@bp.delete("/categories/<int:category_id>")
@api_key_required
def categories_delete(category_id):
    category = db.get_or_404(Category, category_id)
    if category.products:
        return jsonify(error="Tiene productos, no se puede eliminar"), 409   # 409 = Conflict
    db.session.delete(category)
    db.session.commit()
    return "", 204                                      # 204 = No Content


# ---------------------------------------------------------------- products
@bp.get("/products")
@api_key_required
def products_index():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    in_stock = request.args.get("in_stock") == "1"
    per_page = min(request.args.get("per_page", 10, type=int), 100)   # cap it

    stmt = db.select(Product).options(joinedload(Product.category)).order_by(Product.name)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if in_stock:
        stmt = stmt.where(Product.stock > 0)

    page = db.paginate(stmt, per_page=per_page, error_out=False)
    return jsonify({
        "data": [p.to_dict() for p in page.items],
        "meta": {"page": page.page, "per_page": page.per_page,
                 "total": page.total, "pages": page.pages},
    })


@bp.get("/products/<int:product_id>")
@api_key_required
def products_show(product_id):
    return jsonify(db.get_or_404(Product, product_id).to_dict())


@bp.post("/products")
@api_key_required
def products_create():
    clean, errors = validate_product(get_json())
    if errors:
        return jsonify(errors=errors), 422             # 422 = invalid data
    product = Product(**clean)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@bp.put("/products/<int:product_id>")
@api_key_required
def products_update(product_id):
    product = db.get_or_404(Product, product_id)
    clean, errors = validate_product(get_json(), partial=True)
    if errors:
        return jsonify(errors=errors), 422
    for field, value in clean.items():                 # only the fields that came
        setattr(product, field, value)
    db.session.commit()
    return jsonify(product.to_dict())


@bp.delete("/products/<int:product_id>")
@api_key_required
def products_delete(product_id):
    product = db.get_or_404(Product, product_id)
    db.session.delete(product)
    db.session.commit()
    return "", 204
