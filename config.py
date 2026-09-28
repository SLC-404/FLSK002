"""CONFIGURACIÓN por entornos (capítulo 7).

Lo secreto (SECRET_KEY, DATABASE_URL) viene del archivo .env.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-no-usar-en-produccion")

    # Base de datos: MySQL desde el .env.
    # Si DATABASE_URL no existe, usa SQLite (instance/app.db) para no bloquearte.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")

    # Reconecta si MySQL cerró la conexión por inactividad (evita "MySQL server has gone away")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    NOMBRE_APP = "FLSK BASE"

    # ARCHIVOS SUBIDOS
    # Límite total por petición: 5 MB (si mandan algo más grande, Flask responde 413)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    # La carpeta real se calcula en create_app(): instance/uploads/
    # (fuera de static/ para que NADIE pueda abrir los archivos sin permiso)
    UPLOAD_SUBCARPETA = "uploads"


class DevConfig(Config):
    DEBUG = True
    # Cambia a True para ver en la terminal todo el SQL que se ejecuta
    SQLALCHEMY_ECHO = False


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProdConfig(Config):
    DEBUG = False


config = {
    "dev": DevConfig,
    "test": TestConfig,
    "prod": ProdConfig,
}
