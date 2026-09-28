"""CATEGORIES CRUD (protected by view/create/edit/delete-categories)."""
from flask import flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import func

from app.categories import bp
from app.categories.forms import CategoryForm
from app.extensions import db
from app.models import Category, Product
from app.utils.decorators import permission_required


@bp.get("/")
@login_required
@permission_required("view-categories")
def index():
    # Each category with how many products it has:
    #   SELECT categories.*, COUNT(products.id) FROM categories
    #   LEFT JOIN products ON products.category_id = categories.id
    #   GROUP BY categories.id ORDER BY categories.name
    stmt = (
        db.select(Category, func.count(Product.id).label("total"))
        .outerjoin(Category.products)
        .group_by(Category.id)
        .order_by(Category.name)
    )
    rows = db.session.execute(stmt).all()   # each row = (Category, total) -> execute, not scalars
    return render_template("categories/index.html", rows=rows)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-categories")
def create():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data.strip(),
                            description=form.description.data or None)
        db.session.add(category)
        db.session.commit()
        flash(f"Categoría '{category.name}' creada", "success")
        return redirect(url_for("categories.index"))
    return render_template("categories/form.html", form=form, title="Nueva categoría")


@bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-categories")
def edit(category_id):
    category = db.get_or_404(Category, category_id)          # 404 if it doesn't exist
    form = CategoryForm(obj=category, category_id=category.id)  # obj= preloads the inputs

    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.description = form.description.data or None
        db.session.commit()                  # UPDATE: just change attributes and commit
        flash("Categoría actualizada", "success")
        return redirect(url_for("categories.index"))
    return render_template("categories/form.html", form=form, title="Editar categoría")


@bp.post("/<int:category_id>/delete")
@login_required
@permission_required("delete-categories")
def delete(category_id):
    category = db.get_or_404(Category, category_id)
    if category.products:
        # The FK would fail (products pointing to a category that no longer exists)
        flash(f"No se puede eliminar: tiene {len(category.products)} producto(s)", "danger")
    else:
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f"Categoría '{name}' eliminada", "warning")
    return redirect(url_for("categories.index"))
