"""PRODUCTS CRUD (protected by view/create/edit/delete-products).

The list shows everything from chapter 9 together:
  - WHERE with filters from the URL (?q=lap&category=2&in_stock=1)
  - ORDER BY chosen by the user (?sort=price)
  - JOIN with joinedload (avoids the N+1 problem)
  - Pagination with db.paginate (?page=2)
"""
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Category, Product
from app.products import bp
from app.products.forms import ProductForm
from app.utils.decorators import permission_required

# What the user can sort by -> real column. A whitelist: never put request.args
# straight into order_by.
SORTS = {
    "name": Product.name,
    "price": Product.price,
    "price_desc": Product.price.desc(),
    "stock": Product.stock,
}


@bp.get("/")
@login_required
@permission_required("view-products")
def index():
    # 1. Read the filters from the query string (all optional)
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    in_stock = request.args.get("in_stock") == "1"
    sort = request.args.get("sort", "name")

    # 2. Build the query step by step (each .where() adds an AND)
    stmt = db.select(Product).options(joinedload(Product.category))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))           # LIKE '%q%'
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if in_stock:
        stmt = stmt.where(Product.stock > 0)                      # the 9.7 query
    stmt = stmt.order_by(SORTS.get(sort, Product.name))

    # 3. Paginate: 10 per page. page comes from ?page=N; error_out=False -> no 404 if too big
    pagination = db.paginate(stmt, per_page=10, error_out=False)

    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return render_template("products/index.html", pagination=pagination,
                           categories=categories, q=q, category_id=category_id,
                           in_stock=in_stock, sort=sort)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-products")
def create():
    form = ProductForm()
    if not form.category_id.choices:
        flash("Primero crea al menos una categoría", "warning")
        return redirect(url_for("categories.index"))

    if form.validate_on_submit():
        product = Product()
        form.populate_obj(product)   # copies every field with the same name: name, price...
        product.description = product.description or None
        db.session.add(product)
        db.session.commit()
        flash(f"Producto '{product.name}' creado", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, title="Nuevo producto")


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-products")
def edit(product_id):
    product = db.get_or_404(Product, product_id)
    form = ProductForm(obj=product)       # preloads inputs AND selects its category

    if form.validate_on_submit():
        form.populate_obj(product)        # the opposite of obj=: form -> object
        product.description = product.description or None
        db.session.commit()
        flash("Producto actualizado", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, title="Editar producto")


@bp.post("/<int:product_id>/delete")
@login_required
@permission_required("delete-products")
def delete(product_id):
    product = db.get_or_404(Product, product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Producto '{name}' eliminado", "warning")
    return redirect(request.referrer or url_for("products.index"))
