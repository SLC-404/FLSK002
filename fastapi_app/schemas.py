"""SCHEMAS (Pydantic): what comes IN and what goes OUT of the API.

This is the big difference with Flask: here you don't validate by hand.
You declare the shape of the data and FastAPI:
  - validates the JSON automatically (422 with the detail if something is wrong)
  - converts types ("350" -> 350)
  - documents everything in /docs

Typical convention:
  XxxCreate  -> body of POST   (required fields)
  XxxUpdate  -> body of PUT    (everything optional)
  XxxOut     -> response       (includes id; from_attributes lets it read SQLAlchemy objects)
"""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------- categories
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=250)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=250)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # read from a SQLAlchemy object

    id: int
    name: str
    description: str | None


# ---------- products
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=250)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=250)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    category_id: int | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: float
    stock: int
    category: CategoryOut          # nested object


class ProductPage(BaseModel):
    data: list[ProductOut]
    total: int
    page: int
    per_page: int
