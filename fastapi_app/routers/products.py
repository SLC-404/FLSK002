"""PRODUCTS ENDPOINTS (with filters and pagination as query params)."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from fastapi_app.database import get_db
from fastapi_app.models import Category, Product
from fastapi_app.schemas import ProductCreate, ProductOut, ProductPage, ProductUpdate
from fastapi_app.security import api_key_required

router = APIRouter(prefix="/products", tags=["products"],
                   dependencies=[Depends(api_key_required)])


def get_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id, options=[joinedload(Product.category)])
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def check_category(db: Session, category_id: int):
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="La categoría no existe")


@router.get("", response_model=ProductPage)
def index(
    # Query params, declared as function parameters, with validation included:
    q: str | None = None,
    category: int | None = None,
    in_stock: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Product)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Product.category_id == category)
    if in_stock:
        stmt = stmt.where(Product.stock > 0)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))   # COUNT(*)
    items = db.scalars(
        stmt.options(joinedload(Product.category))
        .order_by(Product.name)
        .limit(per_page).offset((page - 1) * per_page)       # manual pagination
    ).all()
    return {"data": items, "total": total, "page": page, "per_page": per_page}


@router.get("/{product_id}", response_model=ProductOut)
def show(product_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create(data: ProductCreate, db: Session = Depends(get_db)):
    check_category(db, data.category_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    return get_or_404(db, product.id)       # reload with its category


@router.put("/{product_id}", response_model=ProductOut)
def update(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = get_or_404(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        check_category(db, changes["category_id"])
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    return get_or_404(db, product.id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(product_id: int, db: Session = Depends(get_db)):
    product = get_or_404(db, product_id)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
