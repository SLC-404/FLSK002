"""EXTENSIONS: created here (empty) and wired up in create_app() with init_app()."""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()               # ORM (models, session, queries)
migrate = Migrate()             # migrations: "flask db ..." commands
csrf = CSRFProtect()            # CSRF protection on every POST form
login_manager = LoginManager()  # who is logged in

login_manager.login_view = "auth.login"            # where to send guests
login_manager.login_message = "Inicia sesión para ver esta página."
login_manager.login_message_category = "warning"   # flash color
