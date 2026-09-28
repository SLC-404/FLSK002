"""MODELOS: Permiso, Rol y Usuario.

Cadena de permisos:   Permiso  <-- N:M -->  Rol  <-- 1:N -->  Usuario
  - Un ROL tiene MUCHOS permisos y un PERMISO está en MUCHOS roles (tabla rol_permisos).
  - Un USUARIO tiene UN rol, y "hereda" los permisos de ese rol.

Relación 1 a N (capítulo 9.5):  un Rol tiene MUCHOS usuarios,
                                cada Usuario tiene UN rol.
  - Usuario.rol_id   -> columna REAL (llave foránea), va en el lado "muchos"
  - Usuario.rol      -> atajo de Python: el objeto Rol     (belongsTo)
  - Rol.usuarios     -> atajo de Python: lista de usuarios (hasMany)
"""
from datetime import datetime

from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


# TABLA INTERMEDIA N:M (capítulo 9.5): solo guarda parejas (rol_id, permiso_id).
# No es clase porque no tiene datos extra; la usamos con secondary= en las relaciones.
rol_permisos = Table(
    "rol_permisos",
    db.metadata,
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True),
)

class Category(db.Model):
    __tablename__="category"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(250))
    
    products:Mapped[list["Products"]]=relationship("category")
    
class Products(db.Model):
    __tablename__="products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))      # "ver-usuarios"
    descripcion: Mapped[str | None] = mapped_column(String(250))
    price: Mapped[int]
    quantity: Mapped[int]
    
    category_id: Mapped[int]= mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"]= relationship(back_populates="category")

    
class Permiso(db.Model):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)      # "ver-usuarios"
    descripcion: Mapped[str | None] = mapped_column(String(150))

    roles: Mapped[list["Rol"]] = relationship(secondary=rol_permisos, back_populates="permisos")

    @property
    def modulo(self):
        """'ver-usuarios' -> 'usuarios'  (para agrupar en pantalla)."""
        return self.nombre.split("-", 1)[-1]

    def __repr__(self):
        return f"<Permiso {self.nombre}>"


class Rol(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)      # "admin", "usuario"
    descripcion: Mapped[str | None] = mapped_column(String(150))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")
    permisos: Mapped[list["Permiso"]] = relationship(secondary=rol_permisos, back_populates="roles",
                                                     order_by="Permiso.nombre")

    def __repr__(self):
        return f"<Rol {self.nombre}>"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))   # nunca la contraseña, solo su hash
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(default=datetime.now)

    # ARCHIVOS: en la BD solo se guarda el NOMBRE del archivo, no el archivo.
    # El archivo vive en instance/uploads/fotos/ o instance/uploads/identificaciones/
    foto: Mapped[str | None] = mapped_column(String(100))
    identificacion: Mapped[str | None] = mapped_column(String(100))
    identificacion_nombre: Mapped[str | None] = mapped_column(String(150))  # nombre original

    # RELACIÓN con Rol
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    rol: Mapped["Rol"] = relationship(back_populates="usuarios")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def tiene_rol(self, *nombres):
        """usuario.tiene_rol("admin")  o  usuario.tiene_rol("admin", "supervisor")"""
        return self.rol is not None and self.rol.nombre in nombres

    def puede(self, permiso):
        """usuario.puede("ver-usuarios") -> True/False según los permisos de SU rol.
        En plantillas:  {% if current_user.puede("crear-usuarios") %} ... {% endif %}"""
        return self.rol is not None and any(p.nombre == permiso for p in self.rol.permisos)

    @property
    def es_admin(self):
        return self.tiene_rol("admin")

    @property
    def is_active(self):
        return self.activo

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Anonimo(AnonymousUserMixin):
    def puede(self, permiso):
        return False


login_manager.anonymous_user = Anonimo


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
