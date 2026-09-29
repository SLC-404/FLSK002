"""MODELS: Permission, Role, User, Category and Product.

Permission chain:   Permission  <-- N:M -->  Role  <-- 1:N -->  User
  - A ROLE has MANY permissions and a PERMISSION belongs to MANY roles (role_permissions table).
  - A USER has ONE role and "inherits" that role's permissions.
"""
from datetime import datetime
from decimal import Decimal

from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy import Column, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

# N:M PIVOT TABLE: only stores (role_id, permission_id) pairs.
# Not a class because it has no extra data; used with secondary= in the relationships.
role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(db.Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)       # "view-users"
    description: Mapped[str | None] = mapped_column(String(150))

    roles: Mapped[list["Role"]] = relationship(secondary=role_permissions,
                                               back_populates="permissions")

    @property
    def module(self):
        """'view-users' -> 'users'  (used to group them on screen)."""
        return self.name.split("-", 1)[-1]

    def __repr__(self):
        return f"<Permission {self.name}>"


class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)       # "admin", "user"
    description: Mapped[str | None] = mapped_column(String(150))

    users: Mapped[list["User"]] = relationship(back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(secondary=role_permissions,
                                                           back_populates="roles",
                                                           order_by="Permission.name")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))   # never the password, only its hash
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # FILES: the DB only stores the file NAME. The file lives in
    # instance/uploads/photos/ or instance/uploads/id_documents/
    photo: Mapped[str | None] = mapped_column(String(100))
    id_document: Mapped[str | None] = mapped_column(String(100))
    id_document_name: Mapped[str | None] = mapped_column(String(150))   # original file name

    # Relationship with Role
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped["Role"] = relationship(back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *names):
        """user.has_role("admin")  or  user.has_role("admin", "supervisor")"""
        return self.role is not None and self.role.name in names

    def can(self, permission):
        """user.can("view-users") -> True/False based on the permissions of THEIR role.
        In templates:  {% if current_user.can("create-users") %} ... {% endif %}"""
        return self.role is not None and any(p.name == permission for p in self.role.permissions)

    @property
    def is_admin(self):
        return self.has_role("admin")

    @property
    def is_active(self):
        """Flask-Login does not let disabled users log in."""
        return self.active

    def __repr__(self):
        return f"<User {self.email}>"


# ---------------------------------------------------------------------------
# PRACTICE 9.7: Category 1 --- N Product
#   - Product.category_id -> REAL column (foreign key), goes on the "many" side
#   - Product.category    -> Python shortcut: the Category object      (belongsTo)
#   - Category.products   -> Python shortcut: list of its products     (hasMany)
#   back_populates connects both sides: each one names the OTHER attribute.
# ---------------------------------------------------------------------------
class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(250))

    products: Mapped[list["Product"]] = relationship(back_populates="category")

    def to_dict(self):
        """Model -> dict, so the API can return it as JSON."""
        return {"id": self.id, "name": self.name, "description": self.description}

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(250))
    # Numeric(10, 2): exact money (up to 99,999,999.99). Python gives you a Decimal.
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(default=0)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="products")

    def to_dict(self):
        """Model -> dict for the API. Decimal is not JSON: convert it to float."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": self.stock,
            "category": {"id": self.category.id, "name": self.category.name},
        }

    def __repr__(self):
        return f"<Product {self.name} ${self.price}>"


class Guest(AnonymousUserMixin):
    """Logged-out user: can't do anything (so current_user.can() never crashes)."""
    def can(self, permission):
        return False


login_manager.anonymous_user = Guest


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
