"""MODELOS: Rol y Usuario.

Relación 1 a N (capítulo 9.5):  un Rol tiene MUCHOS usuarios,
                                cada Usuario tiene UN rol.
  - Usuario.rol_id   -> columna REAL (llave foránea), va en el lado "muchos"
  - Usuario.rol      -> atajo de Python: el objeto Rol     (belongsTo)
  - Rol.usuarios     -> atajo de Python: lista de usuarios (hasMany)
"""
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class Rol(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)      # "admin", "usuario"
    descripcion: Mapped[str | None] = mapped_column(String(150))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")

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

    @property
    def es_admin(self):
        return self.tiene_rol("admin")

    @property
    def is_active(self):
        """Flask-Login no deja entrar a usuarios desactivados."""
        return self.activo

    def __repr__(self):
        return f"<Usuario {self.email}>"


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
