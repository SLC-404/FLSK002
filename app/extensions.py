"""EXTENSIONES: se CREAN aquí (vacías) y se CONECTAN en create_app() con init_app()."""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()             # ORM (modelos, sesión, consultas)
migrate = Migrate()           # migraciones: comandos "flask db ..."
csrf = CSRFProtect()          # protección CSRF en todos los formularios POST
login_manager = LoginManager()  # NUEVO: maneja quién tiene la sesión iniciada

# Configuración de Flask-Login:
login_manager.login_view = "auth.login"   # a dónde mandar si no ha iniciado sesión
login_manager.login_message = "Inicia sesión para ver esta página."
login_manager.login_message_category = "warning"   # color del mensaje flash
