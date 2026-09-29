"""CONFIGURATION per environment.

Secrets (SECRET_KEY, DATABASE_URL) come from the .env file.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-do-not-use-in-production")

    # Database: MySQL from .env. Falls back to SQLite if DATABASE_URL is missing.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")

    # Reconnect if MySQL closed an idle connection ("MySQL server has gone away")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    APP_NAME = "FLSK BASE"

    # REST API (/api/...): clients send it in the "X-API-Key" header.
    # If it's empty, the API is open (handy in development; ALWAYS set it in production).
    API_KEY = os.getenv("API_KEY", "")

    # UPLOADS
    # Max size per request: 5 MB (bigger requests get a 413)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    # Real folder is built in create_app(): instance/uploads/
    # (outside static/ so nobody can open files without permission)
    UPLOAD_SUBFOLDER = "uploads"


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False   # True = print every SQL query in the terminal


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
