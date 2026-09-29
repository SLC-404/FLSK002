# FLSK001 — Guía para la prueba técnica (Flask + FastAPI)

Proyecto base en **Flask 3** con MySQL, login, usuarios, roles, permisos, CRUD de
categorías/productos, **API REST en Flask** y **API en FastAPI** sobre la misma base.

> La instalación paso a paso (Mac, Windows y producción) está en **`.env.example`**.
> Este README es la **guía de qué puede venir en el examen y cómo resolverlo**.

## Índice

1. [Estructura del proyecto](#1-estructura-del-proyecto)
2. [Arranque rápido](#2-arranque-rápido)
3. [Cómo viaja una petición](#3-cómo-viaja-una-petición)
4. [Crear un módulo nuevo (receta completa)](#4-crear-un-módulo-nuevo-receta-completa)
5. [Modelos: estructura correcta](#5-modelos-estructura-correcta)
6. [Consultas (chuleta)](#6-consultas-chuleta)
7. [Vistas: rutas + plantillas](#7-vistas-rutas--plantillas)
8. [Formularios y validaciones](#8-formularios-y-validaciones)
9. [APIs: Flask `/api` y FastAPI](#9-apis-flask-api-y-fastapi)
10. [Conectarse a una base de datos EXISTENTE](#10-conectarse-a-una-base-de-datos-existente)
11. [Qué puede venir en el examen y cómo resolverlo](#11-qué-puede-venir-en-el-examen-y-cómo-resolverlo)
12. [Preguntas teóricas típicas](#12-preguntas-teóricas-típicas)
13. [Git](#13-git)
14. [Errores comunes](#14-errores-comunes)

---

## 1. Estructura del proyecto

```text
FLSK001/
├── .env                  # secretos (NO se sube a Git)
├── .env.example          # plantilla del .env + GUÍA DE INSTALACIÓN
├── .flaskenv             # FLASK_APP=run.py (sí se sube)
├── config.py             # configuración por entorno (dev / test / prod)
├── run.py                # punto de entrada: flask run / gunicorn / waitress
├── requirements.txt
├── migrations/           # Alembic: historial de cambios de la BD
│   └── versions/         # un archivo por cada "flask db migrate"
├── app/
│   ├── __init__.py       # create_app(): extensiones, blueprints, errores, comandos CLI
│   ├── extensions.py     # db, migrate, csrf, login_manager (se crean vacías aquí)
│   ├── models.py         # TODOS los modelos (tablas)
│   ├── utils/            # decorators.py (permisos, api key), files.py, fields.py
│   ├── auth/             # login, registro, logout
│   ├── main/             # inicio y dashboard
│   ├── profile/          # mi perfil + archivos privados
│   ├── users/  roles/  permissions/     # administración
│   ├── categories/  products/           # módulos de ejemplo (práctica 9.7)
│   │     ├── __init__.py   -> crea el Blueprint
│   │     ├── forms.py      -> formularios (WTForms)
│   │     └── routes.py     -> rutas / controlador
│   ├── api/              # API REST JSON de Flask (/api/...)
│   └── templates/        # HTML (Jinja2): layout.html, _form.html y una carpeta por módulo
└── fastapi_app/          # API con FastAPI (otro servidor, misma BD)
    ├── database.py       # engine, SessionLocal, get_db
    ├── models.py         # modelos SQLAlchemy "puros"
    ├── schemas.py        # Pydantic: validación de entrada/salida
    ├── security.py       # API key como dependencia
    ├── routers/          # categories.py, products.py (como blueprints)
    └── main.py           # app = FastAPI()
```

**Equivalencias con Laravel** (para ubicarte rápido):

| Flask | Laravel |
|---|---|
| `models.py` | `app/Models` |
| `flask db migrate` / `upgrade` | `make:migration` / `migrate` |
| Blueprint (`routes.py`) | Controller + `routes/web.php` |
| `forms.py` (WTForms) | Form Request (validación) |
| `templates/*.html` (Jinja) | Blade |
| `@login_required` | `middleware('auth')` |
| `@permission_required("x")` | `middleware('permission:x')` (Spatie) |
| `flask seed` | `db:seed` |
| `flask shell` | `tinker` |
| `.env` + `config.py` | `.env` + `config/` |

---

## 2. Arranque rápido

```bash
git clone <url> && cd FLSK001
python3 -m venv env && source env/bin/activate      # Windows: python -m venv env ; env\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # Windows: copy .env.example .env  -> editar DATABASE_URL
flask db upgrade                                     # crea las tablas
flask seed                                           # permisos + roles
flask create-user                                    # primer admin
flask run                                            # web + API Flask  -> http://127.0.0.1:5000
uvicorn fastapi_app.main:app --reload --port 8001    # (opcional) FastAPI -> http://127.0.0.1:8001/docs
```

Comandos que más vas a usar:

| Comando | Para qué |
|---|---|
| `flask run` | Levantar en desarrollo |
| `flask routes` | Ver TODAS las rutas registradas (útil para `BuildError`) |
| `flask shell` | Consola con `db`, `User`, `Category`, `Product`… ya cargados |
| `flask db migrate -m "msg"` | Generar migración a partir de los modelos |
| `flask db upgrade` / `downgrade` | Aplicar / revertir migraciones |
| `flask db current` / `history` | Ver en qué migración está la BD |
| `flask seed` | Crear permisos y roles (no duplica) |
| `flask create-user` | Crear usuario desde la terminal |

---

## 3. Cómo viaja una petición

```text
Navegador  GET /products/?q=lap
   │
   ▼
Blueprint "products" (url_prefix="/products")  ->  @bp.get("/")  ->  def index()
   │   @login_required           ¿inició sesión?          (si no -> /auth/login)
   │   @permission_required(...) ¿su rol tiene el permiso? (si no -> 403)
   ▼
Lee filtros: request.args.get("q")
   ▼
Consulta: db.select(Product).where(...)  ->  db.session.scalars(...) / db.paginate(...)
   ▼
render_template("products/index.html", ...)   ->  HTML   (o jsonify(...) en la API)
```

Formulario (POST) → patrón **PRG** (Post / Redirect / Get):

```text
GET  /products/new       -> muestra el form
POST /products/new       -> form.validate_on_submit()
        ├─ inválido -> vuelve a mostrar el form con errores (status 200)
        └─ válido   -> guarda, commit, flash("..."), redirect(url_for("products.index"))
```

---

## 4. Crear un módulo nuevo (receta completa)

Ejemplo: **proveedores** (`Supplier`). Copia y cambia nombres. Orden recomendado:

| # | Qué | Dónde |
|---|---|---|
| 1 | Modelo | `app/models.py` |
| 2 | Migración | `flask db migrate -m "suppliers"` → **revisar** → `flask db upgrade` |
| 3 | Permisos | agregar `"suppliers"` a `MODULES` en `app/permissions/catalog.py` → `flask seed` |
| 4 | Blueprint | `app/suppliers/__init__.py` |
| 5 | Formulario | `app/suppliers/forms.py` |
| 6 | Rutas CRUD | `app/suppliers/routes.py` |
| 7 | Plantillas | `app/templates/suppliers/index.html` y `form.html` |
| 8 | Registrar | `app/__init__.py` (import + `register_blueprint`) |
| 9 | Menú | link en `app/templates/layout.html` |
| 10 | (Opcional) API | endpoints en `app/api/routes.py` y/o router en `fastapi_app/` |
| 11 | Git | `git add -A && git commit -m "Suppliers module"` |

### 4.1 Modelo (`app/models.py`)

```python
class Supplier(db.Model):
    __tablename__ = "suppliers"                                   # tabla en plural

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)   # obligatorio (NOT NULL)
    email: Mapped[str | None] = mapped_column(String(120))        # | None -> NULL permitido
    phone: Mapped[str | None] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    def to_dict(self):                                            # para la API
        return {"id": self.id, "name": self.name, "email": self.email,
                "phone": self.phone, "active": self.active}

    def __repr__(self):
        return f"<Supplier {self.name}>"
```

Agrégalo también al `shell_context_processor` de `app/__init__.py` si lo quieres en `flask shell`.

### 4.2 Migración

```bash
flask db migrate -m "suppliers"
# ABRIR migrations/versions/xxxx_suppliers.py y revisar que haga lo que esperas
flask db upgrade
```

### 4.3 Permisos (`app/permissions/catalog.py`)

```python
MODULES = ["permissions", "roles", "users", "categories", "products", "suppliers"]
```

```bash
flask seed      # crea view-/create-/edit-/delete-suppliers y se los da al admin
```

### 4.4 Blueprint (`app/suppliers/__init__.py`)

```python
from flask import Blueprint

bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")

from app.suppliers import routes  # noqa: E402, F401   (al final: evita import circular)
```

### 4.5 Formulario (`app/suppliers/forms.py`)

```python
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from app.extensions import db
from app.models import Supplier


class SupplierForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(message="Obligatorio"), Length(max=120)])
    email = EmailField("Correo", validators=[Optional(), Email(message="Correo no válido")])
    phone = StringField("Teléfono", validators=[Optional(), Length(max=20)])
    active = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")

    def __init__(self, *args, supplier_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.supplier_id = supplier_id                 # None = creando, número = editando

    def validate_name(self, field):                    # validate_<campo> se llama solo
        stmt = db.select(Supplier).where(Supplier.name == field.data.strip())
        if self.supplier_id:
            stmt = stmt.where(Supplier.id != self.supplier_id)
        if db.session.scalar(stmt):
            raise ValidationError("Ya existe")
```

### 4.6 Rutas CRUD (`app/suppliers/routes.py`)

```python
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Supplier
from app.suppliers import bp
from app.suppliers.forms import SupplierForm
from app.utils.decorators import permission_required


@bp.get("/")
@login_required
@permission_required("view-suppliers")
def index():
    q = request.args.get("q", "").strip()
    stmt = db.select(Supplier).order_by(Supplier.name)
    if q:
        stmt = stmt.where(Supplier.name.ilike(f"%{q}%"))
    pagination = db.paginate(stmt, per_page=10, error_out=False)
    return render_template("suppliers/index.html", pagination=pagination, q=q)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@permission_required("create-suppliers")
def create():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier()
        form.populate_obj(supplier)          # copia name, email, phone, active al objeto
        db.session.add(supplier)
        db.session.commit()
        flash("Proveedor creado", "success")
        return redirect(url_for("suppliers.index"))
    return render_template("suppliers/form.html", form=form, title="Nuevo proveedor")


@bp.route("/<int:supplier_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("edit-suppliers")
def edit(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)
    form = SupplierForm(obj=supplier, supplier_id=supplier.id)   # obj= precarga los inputs
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        flash("Proveedor actualizado", "success")
        return redirect(url_for("suppliers.index"))
    return render_template("suppliers/form.html", form=form, title="Editar proveedor")


@bp.post("/<int:supplier_id>/delete")                  # borrar SIEMPRE por POST (con CSRF)
@login_required
@permission_required("delete-suppliers")
def delete(supplier_id):
    supplier = db.get_or_404(Supplier, supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    flash("Proveedor eliminado", "warning")
    return redirect(url_for("suppliers.index"))
```

### 4.7 Plantillas

`app/templates/suppliers/index.html`

```html
{% extends "layout.html" %}
{% block title %}Proveedores{% endblock %}
{% block content %}
  <div class="d-flex justify-content-between mb-3">
    <h1>Proveedores</h1>
    {% if current_user.can("create-suppliers") %}
      <a class="btn btn-primary" href="{{ url_for('suppliers.create') }}">+ Nuevo</a>
    {% endif %}
  </div>

  <form method="get" class="d-flex gap-2 mb-3">
    <input class="form-control" name="q" value="{{ q }}" placeholder="Buscar">
    <button class="btn btn-outline-secondary">Buscar</button>
  </form>

  <table class="table bg-white">
    <thead><tr><th>Nombre</th><th>Correo</th><th>Teléfono</th><th></th></tr></thead>
    <tbody>
    {% for s in pagination.items %}
      <tr>
        <td>{{ s.name }}</td><td>{{ s.email or "—" }}</td><td>{{ s.phone or "—" }}</td>
        <td class="text-end">
          <a class="btn btn-sm btn-warning" href="{{ url_for('suppliers.edit', supplier_id=s.id) }}">Editar</a>
          <form method="post" action="{{ url_for('suppliers.delete', supplier_id=s.id) }}"
                class="d-inline" onsubmit="return confirm('¿Eliminar?')">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <button class="btn btn-sm btn-danger">Eliminar</button>
          </form>
        </td>
      </tr>
    {% else %}
      <tr><td colspan="4" class="text-center text-muted">Sin registros</td></tr>
    {% endfor %}
    </tbody>
  </table>
{% endblock %}
```

`app/templates/suppliers/form.html`

```html
{% extends "layout.html" %}
{% from "_form.html" import field %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
  <h1>{{ title }}</h1>
  <form method="post" novalidate class="card card-body col-md-6">
    {{ form.hidden_tag() }}            {# token CSRF: SIN esto el POST falla con 400 #}
    {{ field(form.name) }}
    {{ field(form.email) }}
    {{ field(form.phone) }}
    {{ field(form.active) }}
    {{ form.submit(class="btn btn-success") }}
  </form>
{% endblock %}
```

La paginación completa (con números de página y conservando filtros) está en
`app/templates/products/index.html`: cópiala de ahí.

### 4.8 Registrar y agregar al menú

`app/__init__.py`:

```python
from app.suppliers import bp as suppliers_bp
app.register_blueprint(suppliers_bp)
```

`app/templates/layout.html`:

```html
{% if current_user.can("view-suppliers") %}
  <a class="nav-link" href="{{ url_for('suppliers.index') }}">Proveedores</a>
{% endif %}
```

Checa con `flask routes` que aparezcan `suppliers.index`, `suppliers.create`, etc.

---

## 5. Modelos: estructura correcta

### 5.1 Reglas

- **Clase en singular y PascalCase** (`Product`), **tabla en plural y snake_case** (`products`).
- Todo `Mapped[...]` es una **columna**, excepto lo que sea `relationship(...)`.
- `Mapped[str]` → `NOT NULL`. `Mapped[str | None]` → permite `NULL`.
- La **llave foránea** (`xxx_id`) va del lado **"muchos"**.
- `relationship` **no crea columnas**: es un atajo de Python para navegar.
- Cada cambio en modelos → `flask db migrate` + revisar + `flask db upgrade`.

### 5.2 Tipos de columna

```python
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func

id: Mapped[int] = mapped_column(primary_key=True)                 # INT AUTO_INCREMENT PK
name: Mapped[str] = mapped_column(String(100))                    # VARCHAR(100) NOT NULL
notes: Mapped[str | None] = mapped_column(Text)                   # TEXT NULL
price: Mapped[Decimal] = mapped_column(Numeric(10, 2))            # DECIMAL(10,2)  (dinero)
stock: Mapped[int] = mapped_column(default=0)                     # INT con default en Python
active: Mapped[bool] = mapped_column(default=True)                # TINYINT(1) / BOOLEAN
birthday: Mapped[date | None]                                     # DATE
created_at: Mapped[datetime] = mapped_column(default=datetime.now)          # lo pone Python
updated_at: Mapped[datetime] = mapped_column(server_default=func.now(),     # lo pone la BD
                                             onupdate=func.now())
email: Mapped[str] = mapped_column(String(120), unique=True, index=True)    # único + índice
status: Mapped[str] = mapped_column(Enum("pending", "paid", "cancelled", name="order_status"),
                                    default="pending")
```

| Python | SQLAlchemy | MySQL |
|---|---|---|
| `int` | `Integer` | INT |
| `str` | `String(n)` / `Text` | VARCHAR(n) / TEXT |
| `Decimal` | `Numeric(p, s)` | DECIMAL(p,s) |
| `float` | `Float` | FLOAT/DOUBLE (**no** para dinero) |
| `bool` | `Boolean` | TINYINT(1) |
| `date` / `datetime` | `Date` / `DateTime` | DATE / DATETIME |

### 5.3 Relación 1 a N (una categoría → muchos productos)

```python
class Category(db.Model):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    products: Mapped[list["Product"]] = relationship(back_populates="category")   # hasMany


class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))         # columna REAL
    category: Mapped["Category"] = relationship(back_populates="products")        # belongsTo
```

`back_populates` = **el nombre del atributo del OTRO lado**.

Borrar hijos junto con el padre (ej. pedido → sus renglones):

```python
items: Mapped[list["OrderItem"]] = relationship(back_populates="order",
                                                cascade="all, delete-orphan")
```

### 5.4 Relación 1 a 1 (usuario → perfil)

```python
class User(db.Model):
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)

class Profile(db.Model):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)   # unique = 1:1
    user: Mapped["User"] = relationship(back_populates="profile")
```

### 5.5 Relación N a M simple (tabla pivote) — roles ↔ permisos

```python
role_permissions = Table(
    "role_permissions", db.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(db.Model):
    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions,
                                                           back_populates="roles")
class Permission(db.Model):
    roles: Mapped[list["Role"]] = relationship(secondary=role_permissions,
                                               back_populates="permissions")

role.permissions.append(p)        # INSERT en la pivote
role.permissions = [p1, p2]       # "sync"
```

### 5.6 N a M CON datos extra (pedido ↔ producto con cantidad y precio)

Cuando la pivote necesita columnas propias, se vuelve **modelo** (association object):

```python
class Order(db.Model):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order",
                                                    cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(i.quantity * i.unit_price for i in self.items)


class OrderItem(db.Model):
    __tablename__ = "order_items"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))   # precio al momento de vender

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

# Uso
order = Order(items=[OrderItem(product=laptop, quantity=2, unit_price=laptop.price)])
db.session.add(order); db.session.commit()
```

### 5.7 Extras útiles en un modelo

```python
@property
def is_available(self):                 # "campo calculado": product.is_available
    return self.stock > 0

def to_dict(self):                      # para jsonify en la API
    return {"id": self.id, "name": self.name, "price": float(self.price)}

__table_args__ = (                      # restricciones a nivel tabla
    db.UniqueConstraint("category_id", "name", name="uq_product_category_name"),
    db.CheckConstraint("stock >= 0", name="ck_stock_positive"),
)
```

---

## 6. Consultas (chuleta)

```python
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload, selectinload

# --- LEER -------------------------------------------------------------------
db.session.get(Product, 5)                               # por PK (None si no existe)
db.get_or_404(Product, 5)                                # por PK (404 si no existe)
db.session.scalars(db.select(Product)).all()             # todos -> lista de objetos
db.session.scalar(db.select(Product).filter_by(name="Mouse"))   # uno o None

stmt = (db.select(Product)
        .where(Product.stock > 0)                        # WHERE
        .where(Product.price.between(100, 1000))         # AND ... BETWEEN
        .where(or_(Product.name.ilike("%lap%"),           # OR + LIKE sin mayúsculas
                   Product.description.ilike("%lap%")))
        .where(Product.category_id.in_([1, 2]))          # IN
        .order_by(Product.price.desc(), Product.name)    # ORDER BY
        .limit(10).offset(20))                           # LIMIT / OFFSET
products = db.session.scalars(stmt).all()

# --- CONTAR / AGRUPAR ----------------------------------------------------------
db.session.scalar(db.select(func.count(Product.id)))                     # COUNT
db.session.scalar(db.select(func.sum(Product.price * Product.stock)))    # SUM (valor inventario)
rows = db.session.execute(                                               # GROUP BY
    db.select(Category.name, func.count(Product.id))
    .outerjoin(Category.products).group_by(Category.id)).all()
for name, total in rows: ...

# --- JOIN ------------------------------------------------------------------------
db.select(Product).join(Product.category).where(Category.name == "Hogar")   # filtrar por la otra tabla
db.select(Product).options(joinedload(Product.category))    # traer la relación (N:1) en el mismo query
db.select(Category).options(selectinload(Category.products))  # traer listas (1:N) sin N+1

# --- PAGINAR -----------------------------------------------------------------------
page = db.paginate(stmt, per_page=10, error_out=False)      # lee ?page= solo
page.items, page.total, page.pages, page.has_next, page.next_num

# --- CREAR / EDITAR / BORRAR -----------------------------------------------------------
p = Product(name="Mouse", price=350, stock=5, category=cat)
db.session.add(p); db.session.commit()                      # INSERT
p.stock = 10; db.session.commit()                           # UPDATE
db.session.delete(p); db.session.commit()                   # DELETE
db.session.rollback()                                       # deshacer si algo falló

# --- MASIVO ----------------------------------------------------------------------------
db.session.execute(db.update(Product).where(Product.stock == 0).values(active=False))
db.session.execute(db.delete(Product).where(Product.stock < 0))
db.session.commit()

# --- SQL CRUDO -------------------------------------------------------------------------
from sqlalchemy import text
rows = db.session.execute(text("SELECT id, name FROM products WHERE price > :p"), {"p": 500}).all()
```

| Método | Regresa | Úsalo cuando |
|---|---|---|
| `scalars(stmt).all()` | lista de objetos | seleccionas UN modelo |
| `scalar(stmt)` | un valor/objeto o None | un registro o un COUNT |
| `execute(stmt).all()` | lista de filas (tuplas) | seleccionas VARIAS cosas (modelo + conteo) |

**N+1:** si en un `for` usas `p.category.name` sin `joinedload`, se hace 1 query extra por producto.

---

## 7. Vistas: rutas + plantillas

### 7.1 Rutas CRUD estándar (igual que un resource de Laravel)

| Método | URL | Función | Qué hace |
|---|---|---|---|
| GET | `/products/` | `index` | lista (filtros por `?q=`) |
| GET / POST | `/products/new` | `create` | form / guardar |
| GET / POST | `/products/<id>/edit` | `edit` | form precargado / actualizar |
| POST | `/products/<id>/delete` | `delete` | borrar (HTML no manda DELETE: se usa POST + CSRF) |

### 7.2 Piezas de una ruta

```python
@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])  # <int:...> = parámetro de ruta
@login_required                                               # 1. sesión
@permission_required("edit-products")                         # 2. permiso
def edit(product_id):
    product = db.get_or_404(Product, product_id)              # 3. buscar o 404
    form = ProductForm(obj=product)                           # 4. form precargado
    if form.validate_on_submit():                             # 5. ¿POST y válido?
        form.populate_obj(product)                            #    form -> objeto
        db.session.commit()                                   #    guardar
        flash("Actualizado", "success")                       #    mensaje
        return redirect(url_for("products.index"))            #    PRG
    return render_template("products/form.html", form=form)   # 6. GET o inválido
```

- **Parámetro de ruta** (`/products/5`) → identifica UN recurso.
- **Query string** (`?q=lap&page=2`) → filtros, búsqueda, orden, paginación: `request.args.get("q")`.
- **Formulario** (POST) → `form.campo.data` (o `request.form["campo"]` sin WTForms).
- **JSON** (API) → `request.get_json()`.

### 7.3 Plantillas (Jinja2)

```html
{% extends "layout.html" %}                          {# hereda el layout #}
{% from "_form.html" import field %}                 {# importa la macro #}
{% block title %}Productos{% endblock %}
{% block content %}
  {{ variable }}                                     {# imprime (escapa HTML solo) #}
  {{ p.price|round(2) }}  {{ nombre|upper }}  {{ lista|length }}   {# filtros #}
  {{ "{:,.2f}".format(p.price) }}                    {# formato de dinero #}
  {% if current_user.can("edit-products") %} ... {% endif %}
  {% for p in products %} ... {% else %} Sin datos {% endfor %}
  <a href="{{ url_for('products.edit', product_id=p.id) }}">Editar</a>   {# NUNCA URLs a mano #}
  {{ field(form.name) }}                             {# input + label + errores #}
{% endblock %}
```

---

## 8. Formularios y validaciones

| Campo | Para | Validadores típicos |
|---|---|---|
| `StringField` | texto | `DataRequired()`, `Length(max=)`, `Regexp()` |
| `TextAreaField` | texto largo | `Optional()`, `Length(max=)` |
| `EmailField` | correo | `Email()` |
| `PasswordField` | contraseña | `Length(min=8)`, `EqualTo("password")` |
| `IntegerField` | entero | `InputRequired()`, `NumberRange(min=0)` |
| `DecimalField(places=2)` | dinero | `InputRequired()`, `NumberRange(min=0)` |
| `DateField` | fecha | `DataRequired()` |
| `BooleanField` | checkbox | — |
| `SelectField(coerce=int)` | select | choices desde la BD en `__init__` |
| `SelectMultipleField` | varios | (ver `CheckboxListField` en roles) |
| `RadioField` | radios | `DataRequired()` |
| `FileField` | archivo | `FileAllowed([...])`, `FileSize(max_size=)` |

Claves:

- `DataRequired` falla con `0` → para números usa **`InputRequired`**.
- `Optional()` al inicio = si viene vacío, no valida lo demás.
- Validación contra la BD (único, existe) → método **`validate_<campo>(self, field)`**.
- Opciones del select desde la BD:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.category_id.choices = [(c.id, c.name) for c in
                                db.session.scalars(db.select(Category).order_by(Category.name))]
```

- Formularios con archivos: `<form method="post" enctype="multipart/form-data">`.
- Todo POST necesita `{{ form.hidden_tag() }}` (o `csrf_token()`) → si no, **400 Bad Request**.

---

## 9. APIs: Flask `/api` y FastAPI

Una API REST recibe y regresa **JSON**, usa los **métodos HTTP** y responde con **códigos de estado**.

| Código | Significa | Cuándo |
|---|---|---|
| 200 OK | todo bien | GET, PUT |
| 201 Created | creado | POST |
| 204 No Content | sin cuerpo | DELETE |
| 400 Bad Request | petición mal formada | JSON inválido |
| 401 Unauthorized | sin credenciales | falta / mala API key o token |
| 403 Forbidden | sin permiso | tiene sesión pero no permiso |
| 404 Not Found | no existe | id inexistente |
| 409 Conflict | choque | borrar categoría con productos |
| 422 Unprocessable | datos inválidos | validación |
| 500 | error del servidor | bug |

Seguridad: las APIs **no** usan la sesión/cookies ni CSRF. Aquí se usa una **API key** en el
header `X-API-Key` (variable `API_KEY` del `.env`; vacía = abierta, solo en desarrollo).
En un sistema real: **JWT** (`flask-jwt-extended` / `python-jose` en FastAPI).

### 9.1 API de Flask (`app/api/routes.py`) — se levanta con `flask run`

| Método | URL | Body |
|---|---|---|
| GET | `/api/categories` | — |
| GET | `/api/categories/<id>` | — |
| POST | `/api/categories` | `{"name": "Oficina", "description": "..."}` |
| PUT | `/api/categories/<id>` | campos a cambiar |
| DELETE | `/api/categories/<id>` | — |
| GET | `/api/products?q=&category=&in_stock=1&page=1&per_page=10` | — |
| GET | `/api/products/<id>` | — |
| POST | `/api/products` | `{"name":"Mouse","price":350,"stock":10,"category_id":1}` |
| PUT | `/api/products/<id>` | solo los campos a cambiar |
| DELETE | `/api/products/<id>` | — |

Patrón de un endpoint Flask:

```python
@bp.post("/products")
@api_key_required
def products_create():
    data = request.get_json(silent=True) or {}         # 1. leer JSON
    clean, errors = validate_product(data)             # 2. validar (a mano)
    if errors:
        return jsonify(errors=errors), 422             # 3. error -> 422
    product = Product(**clean)                         # 4. guardar
    db.session.add(product); db.session.commit()
    return jsonify(product.to_dict()), 201             # 5. responder JSON + código
```

Puntos clave: blueprint con `url_prefix="/api"`, `csrf.exempt(api_bp)` en `create_app`,
`to_dict()` en los modelos (`Decimal` → `float`), y los errores 404/403/405/500 responden JSON
cuando la URL empieza con `/api/`.

### 9.2 FastAPI (`fastapi_app/`) — otro servidor, misma base de datos

```bash
uvicorn fastapi_app.main:app --reload --port 8001
# http://127.0.0.1:8001/docs  -> Swagger: probar todo desde el navegador (botón "Authorize" no
#                                  aplica; pon el header X-API-Key en cada endpoint "Try it out")
```

Mismos endpoints sin `/api`: `/categories`, `/products`, `/products/{id}`…

Las 4 piezas de FastAPI:

```python
# 1) database.py -> conexión + sesión por petición
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2) models.py -> SQLAlchemy "puro" (Base en vez de db.Model), mismas tablas

# 3) schemas.py -> Pydantic: forma de entrada y salida (valida SOLO)
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    category_id: int

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # leer objetos SQLAlchemy
    id: int
    name: str
    price: float

# 4) routers/products.py -> endpoints
router = APIRouter(prefix="/products", tags=["products"],
                   dependencies=[Depends(api_key_required)])

@router.post("", response_model=ProductOut, status_code=201)
def create(data: ProductCreate, db: Session = Depends(get_db)):   # data YA viene validado
    product = Product(**data.model_dump())
    db.add(product); db.commit(); db.refresh(product)
    return product

@router.get("/{product_id}", response_model=ProductOut)
def show(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="No encontrado")
    return product

# main.py
app = FastAPI(title="Mi API")
app.include_router(products.router)
```

Agregar un recurso nuevo en FastAPI: modelo en `fastapi_app/models.py` → schemas
`XxxCreate / XxxUpdate / XxxOut` → `routers/xxx.py` → `app.include_router(xxx.router)` en `main.py`.
(Las tablas las crea Flask con sus migraciones; si FastAPI estuviera solo:
`Base.metadata.create_all(engine)` o Alembic.)

### 9.3 Flask vs FastAPI

| | Flask | FastAPI |
|---|---|---|
| Tipo | micro-framework web (HTML + API) | framework para **APIs** |
| Validación | a mano o WTForms / marshmallow | **automática** con Pydantic (type hints) |
| Documentación | no trae | **automática** en `/docs` y `/redoc` |
| Servidor | WSGI (gunicorn / waitress) | ASGI (**uvicorn**) |
| Async | limitado | nativo (`async def`) |
| Inyección de dependencias | no | `Depends(...)` |
| Organización | Blueprints | APIRouter |
| Parámetros | `request.args.get("q")` | parámetros de la función: `def index(q: str \| None = None)` |
| Body | `request.get_json()` | parámetro tipado: `data: ProductCreate` |
| Error | `abort(404)` / `return jsonify(...), 404` | `raise HTTPException(404, ...)` |

### 9.4 Probar APIs

```bash
# Mac / Linux / Git Bash
curl http://127.0.0.1:5000/api/products -H "X-API-Key: TU_LLAVE"
curl -X POST http://127.0.0.1:5000/api/products -H "Content-Type: application/json" \
     -H "X-API-Key: TU_LLAVE" -d '{"name":"Mouse","price":350,"stock":10,"category_id":1}'
curl -X PUT http://127.0.0.1:5000/api/products/1 -H "Content-Type: application/json" \
     -H "X-API-Key: TU_LLAVE" -d '{"stock":3}'
curl -X DELETE http://127.0.0.1:5000/api/products/1 -H "X-API-Key: TU_LLAVE"
```

```powershell
# Windows PowerShell
Invoke-RestMethod http://127.0.0.1:5000/api/products -Headers @{"X-API-Key"="TU_LLAVE"}
Invoke-RestMethod -Method Post http://127.0.0.1:5000/api/products -Headers @{"X-API-Key"="TU_LLAVE"} `
  -ContentType "application/json" -Body '{"name":"Mouse","price":350,"stock":10,"category_id":1}'
```

También sirven **Postman**, **Insomnia** o la extensión **Thunder Client** de VS Code, y para
FastAPI directamente `/docs`.

---

## 10. Conectarse a una base de datos EXISTENTE

Si te dan una BD que ya tiene tablas y datos, **lo único que cambia la conexión es `DATABASE_URL`**
(y el driver). Lo delicado es **cómo mapear sus tablas** y **no romperlas con migraciones**.

### 10.1 Cadenas de conexión (URI) por motor

Formato general: `motor+driver://usuario:contraseña@host:puerto/base?opciones`

| Motor | Instalar | `DATABASE_URL` |
|---|---|---|
| **MySQL / MariaDB** | `pip install pymysql cryptography` | `mysql+pymysql://user:pass@localhost:3306/mibase?charset=utf8mb4` |
| **PostgreSQL** | `pip install psycopg2-binary` | `postgresql+psycopg2://user:pass@localhost:5432/mibase` |
| PostgreSQL (psycopg 3) | `pip install "psycopg[binary]"` | `postgresql+psycopg://user:pass@localhost:5432/mibase` |
| **SQL Server** (usuario/contraseña) | `pip install pyodbc` + *ODBC Driver 18* | `mssql+pyodbc://user:pass@localhost:1433/mibase?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes` |
| SQL Server (auth. de Windows) | `pip install pyodbc` | `mssql+pyodbc://@MIPC\SQLEXPRESS/mibase?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes` |
| SQL Server (sin ODBC) | `pip install pymssql` | `mssql+pymssql://user:pass@localhost:1433/mibase` |
| **SQLite** | (ya viene) | `sqlite:///app.db` (relativo a `instance/`) o `sqlite:////ruta/absoluta.db` |
| **Oracle** | `pip install oracledb` | `oracle+oracledb://user:pass@localhost:1521/?service_name=XEPDB1` |

Notas:

- **Contraseña con caracteres especiales** (`@ : / # ? &`): codifícala.
  ```python
  from urllib.parse import quote_plus
  print(quote_plus("P@ss:w0rd#"))      # -> P%40ss%3Aw0rd%23   (eso va en la URL)
  ```
- **ODBC Driver para SQL Server**: Windows → descargar "ODBC Driver 18 for SQL Server" de Microsoft;
  Mac → `brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release && brew install msodbcsql18`.
  Ver drivers instalados: `python -c "import pyodbc; print(pyodbc.drivers())"`.
- Instancia con nombre de SQL Server (`SERVIDOR\SQLEXPRESS`): en la URL va `@SERVIDOR\SQLEXPRESS/base`
  (sin puerto) o usa el puerto fijo de la instancia.
- Agrega el driver que uses a `requirements.txt` (`pip freeze > requirements.txt`).

### 10.2 Probar la conexión ANTES de programar

```python
# probar_conexion.py   ->  python probar_conexion.py
from sqlalchemy import create_engine, inspect, text

engine = create_engine("mysql+pymysql://user:pass@localhost:3306/mibase")
with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())          # 1 = conectó
insp = inspect(engine)
print(insp.get_table_names())                               # tablas que existen
for col in insp.get_columns("clientes"):                    # columnas de una tabla
    print(col["name"], col["type"], col["nullable"])
```

Desde Flask: `flask shell` → `db.session.execute(db.text("SELECT 1")).scalar()`.

### 10.3 Opción A — Escribir los modelos a mano (lo más común)

Haces coincidir **nombre de tabla y columnas** con lo que ya existe. El atributo de Python puede
llamarse distinto a la columna real:

```python
class Customer(db.Model):
    __tablename__ = "tbl_clientes"                     # nombre REAL de la tabla
    __table_args__ = {"schema": "ventas"}              # si está en otro esquema (SQL Server / Postgres)

    id: Mapped[int] = mapped_column("IdCliente", primary_key=True)        # columna real "IdCliente"
    name: Mapped[str] = mapped_column("NombreCliente", String(150))
    email: Mapped[str | None] = mapped_column("Correo", String(150))
    created_at: Mapped[datetime | None] = mapped_column("FechaAlta")
```

Solo necesitas mapear las columnas que vas a usar, **pero** la PK siempre.
Una **vista** de la BD se mapea igual (solo lectura), marcando alguna columna como `primary_key=True`.

### 10.4 Opción B — Generar los modelos automáticamente con `sqlacodegen`

```bash
pip install sqlacodegen
sqlacodegen "mysql+pymysql://user:pass@localhost:3306/mibase" > modelos_generados.py
sqlacodegen "mysql+pymysql://..." --tables clientes,pedidos > modelos_generados.py   # solo algunas
```

Genera clases con `Mapped[...]`. Cópialas a `app/models.py` y cambia `Base` por `db.Model`
(y borra la clase `Base` que genera).

### 10.5 Opción C — Reflejar las tablas sin escribir modelos (automap)

```python
from sqlalchemy.ext.automap import automap_base

with app.app_context():                 # o dentro de una ruta
    Base = automap_base()
    Base.prepare(autoload_with=db.engine)
    Cliente = Base.classes.clientes     # clase creada al vuelo desde la tabla
    clientes = db.session.scalars(db.select(Cliente).limit(10)).all()
```

Útil para explorar rápido; para el proyecto real es mejor la opción A o B.

### 10.6 Opción D — SQL directo (consultas complejas, reportes, stored procedures)

```python
from sqlalchemy import text

rows = db.session.execute(
    text("SELECT c.NombreCliente, SUM(p.Total) AS total FROM tbl_clientes c "
         "JOIN tbl_pedidos p ON p.IdCliente = c.IdCliente "
         "WHERE p.Fecha >= :desde GROUP BY c.NombreCliente"),
    {"desde": "2026-01-01"},                          # SIEMPRE parámetros, nunca f-strings (SQL injection)
).mappings().all()                                    # -> lista de dicts: row["total"]

db.session.execute(text("CALL sp_actualiza_stock(:id)"), {"id": 5})       # MySQL
db.session.execute(text("EXEC sp_actualiza_stock :id"), {"id": 5})        # SQL Server
db.session.commit()
```

### 10.7 Migraciones con una BD existente (¡cuidado!)

- **No** corras `flask db migrate` a ciegas: Alembic compara tus modelos con TODA la BD y puede
  generar `drop_table` de las tablas que no mapeaste. **Revisa siempre el archivo generado.**
- Si la BD ya tiene exactamente las tablas de tus modelos: `flask db stamp head`
  (marca las migraciones como aplicadas sin ejecutar nada).
- Si solo vas a **leer/escribir** datos de tablas ajenas: no uses migraciones para esas tablas.
- Si necesitas tablas propias (usuarios, roles…) en una BD ajena, opción segura: ponlas en
  **otra base** con `SQLALCHEMY_BINDS`:

```python
# config.py
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")               # tu BD (usuarios, roles...)
SQLALCHEMY_BINDS = {"erp": os.getenv("ERP_DATABASE_URL")}          # la BD existente

# models.py
class Customer(db.Model):
    __bind_key__ = "erp"                                          # este modelo usa la otra BD
    __tablename__ = "tbl_clientes"
    ...
```

Con binds, Flask-Migrate solo migra la BD principal (salvo que inicies con `flask db init --multidb`),
así que la BD existente queda intacta.

### 10.8 En FastAPI

Igual: solo cambia `DATABASE_URL` en `.env` (lo lee `fastapi_app/database.py`) y mapea los modelos
en `fastapi_app/models.py` con la opción A o B.

---

## 11. Qué puede venir en el examen y cómo resolverlo

Antes de programar: **lee todo el enunciado, pregunta lo que no esté claro, y haz commits pequeños**
(uno por paso). Primero que funcione, luego que se vea bonito.

### "Haz un CRUD de X con conexión a base de datos" (lo más probable)

1. `git clone` de tu base → levantar (sección 2) → confirmar login.
2. Receta de la **sección 4**: modelo → migrate/upgrade → permisos → blueprint → form → rutas → plantillas → registrar → menú.
3. Probar crear / listar / editar / borrar + validaciones (vacío, duplicado, negativo).
4. `git add -A && git commit -m "X CRUD"` → `git push`.

### "Relaciona dos tablas" (ej. productos con categorías, pedidos con clientes)

- FK en el lado "muchos" + `relationship` en ambos lados (5.3).
- En el form: `SelectField(coerce=int)` con opciones de la BD (sección 8).
- En la lista: `joinedload` y mostrar `p.category.name`.
- No dejar borrar el padre si tiene hijos (o usar `cascade`).

### "Agrega búsqueda / filtros / paginación / orden"

- Filtros por GET: `request.args.get(...)` y `.where(...)` condicional (ver `products/routes.py`).
- `db.paginate(stmt, per_page=10)` + la paginación de `templates/products/index.html`.
- Orden con lista blanca (`SORTS` en `products/routes.py`), nunca `order_by(request.args[...])`.

### "Expón una API REST" / "consume los datos desde otro sistema"

- Rápido: agrega endpoints en `app/api/routes.py` (sección 9.1).
- Si piden **FastAPI**: modelo + schemas + router en `fastapi_app/` (sección 9.2) y enseña `/docs`.
- Devuelve códigos correctos (201, 204, 404, 422) y prueba con curl/Postman.

### "Conéctate a esta base de datos que ya existe"

1. Instalar driver (10.1) y poner `DATABASE_URL`.
2. Probar conexión y listar tablas/columnas (10.2).
3. Mapear modelos (10.3 a mano o 10.4 con sqlacodegen). **No** migrar sobre sus tablas (10.7).
4. Hacer el CRUD/consulta pedida sobre esos modelos.

### "Haz un reporte / consulta" (totales, agrupados, top 5…)

- `func.count / func.sum / group_by` (sección 6) o `text()` con parámetros (10.6).
- Mostrar en tabla HTML o devolver JSON.

### "Agrega login / roles / permisos"

- Ya está: `@login_required`, `@permission_required("...")`, `current_user.can("...")`.
- Nuevo permiso: `MODULES` en `catalog.py` → `flask seed` → asignar en Roles → Editar.

### "Sube un archivo"

- Ver `profile/routes.py` + `utils/files.py`: `FileField` + `FileAllowed`, `enctype="multipart/form-data"`,
  nombre con `uuid`, guardar en `instance/uploads`, servir con `send_from_directory`.

### "Súbelo a producción" / "¿cómo lo desplegarías?"

- `.env.example` sección D: `APP_ENV=prod`, SECRET_KEY nueva, `flask db upgrade`,
  gunicorn (Linux/Mac) o waitress (Windows), Nginx/IIS con HTTPS adelante.
- FastAPI: `uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8001 --workers 4`.

### Si te atoras

- `flask routes` (¿existe el endpoint?), revisar la terminal (traceback completo, la ÚLTIMA línea dice el error),
  `flask shell` para probar la consulta aislada, `SQLALCHEMY_ECHO = True` en `config.py` para ver el SQL.
- Explica en voz alta qué estás haciendo: evalúan cómo piensas, no solo el resultado.

---

## 12. Preguntas teóricas típicas

- **¿Qué es un Blueprint?** Un módulo de rutas/plantillas que se registra en la app (como un grupo de rutas + controlador).
- **¿Qué es la application factory?** `create_app()`: crea y configura la app en una función (permite varios entornos y pruebas).
- **ORM:** mapea tablas a clases y filas a objetos. SQLAlchemy usa **Unit of Work** (la sesión junta cambios y los manda en el `commit`); Eloquent usa Active Record (`$model->save()`).
- **`migrate` vs `upgrade`:** `migrate` genera el archivo comparando modelos vs BD; `upgrade` lo ejecuta.
- **Problema N+1:** 1 consulta para la lista + 1 por cada elemento al acceder a la relación. Se arregla con `joinedload`/`selectinload`.
- **CSRF:** ataque que usa tu sesión desde otro sitio. Se evita con un token oculto en cada form (`hidden_tag()`).
- **XSS:** inyectar JS. Jinja escapa `{{ }}` automáticamente (no uses `|safe` con datos del usuario).
- **SQL Injection:** se evita con el ORM o `text()` con parámetros `:param`, nunca concatenando strings.
- **Contraseñas:** nunca en texto plano: `generate_password_hash` / `check_password_hash` (hash con sal).
- **Autenticación vs autorización:** quién eres (login) vs qué puedes hacer (roles/permisos).
- **REST:** recursos con URLs (`/products/5`) + métodos HTTP (GET/POST/PUT/DELETE) + códigos de estado + JSON, sin estado.
- **PUT vs PATCH:** PUT reemplaza el recurso; PATCH cambia algunos campos (aquí el PUT acepta parciales).
- **WSGI vs ASGI:** interfaz servidor↔app síncrona (Flask: gunicorn/waitress) vs asíncrona (FastAPI: uvicorn).
- **¿Por qué FastAPI?** Validación y documentación automáticas con type hints, async, muy rápido. **¿Por qué Flask?** Flexible, maduro, web + API.
- **Pydantic:** valida y convierte datos con clases y type hints.
- **`.env`:** secretos fuera del código y fuera de Git.
- **Índices:** aceleran búsquedas/joins en columnas consultadas (`index=True`, FK, `unique`).
- **Transacción:** todo o nada; `commit()` confirma, `rollback()` deshace.
- **1:N vs N:M:** FK en el lado muchos vs tabla pivote.

---

## 13. Git

```bash
git status                          # qué cambió
git add -A                          # agrega TODO (incluye archivos borrados)
git commit -m "Products CRUD"       # mensaje corto en imperativo
git push                            # subir
git checkout -b feature/suppliers   # rama nueva para un módulo
git log --oneline                   # historial
git diff                            # ver cambios antes del commit
```

`.gitignore` ya excluye `env/`, `.env`, `instance/`, `__pycache__/`. **Nunca subas el `.env`.**

---

## 14. Errores comunes

| Error | Causa → solución |
|---|---|
| `BuildError: Could not build url for endpoint 'x'` | nombre mal en `url_for` o blueprint sin registrar → `flask routes` |
| `TemplateNotFound` | ruta del HTML mal; es relativa a `app/templates/` |
| `400 Bad Request: The CSRF token is missing` | falta `{{ form.hidden_tag() }}` en el form |
| `405 Method Not Allowed` | la ruta no acepta ese método (`methods=["GET","POST"]`) |
| `Table 'x' doesn't exist` | falta `flask db upgrade` |
| `Target database is not up to date` | falta `upgrade` antes de `migrate` |
| `Can't locate revision` | la BD tiene una migración que ya no existe → recrear BD o `flask db stamp head` |
| `1045 Access denied` | usuario/contraseña de `DATABASE_URL` |
| `IntegrityError (FOREIGN KEY / Duplicate entry)` | borrar padre con hijos / valor único repetido → validar antes, `rollback()` |
| `AttributeError: 'NoneType' ...` | `scalar()` no encontró nada → usa `get_or_404` o checa `None` |
| `DetachedInstanceError` | usar un objeto después de cerrar la sesión (FastAPI: `expire_on_commit=False`) |
| `ModuleNotFoundError` | env sin activar o falta `pip install -r requirements.txt` |
| FastAPI `422` al llamar | el JSON no coincide con el schema: lee el `detail` |
| Página sin estilos | sin internet (Bootstrap por CDN) |
