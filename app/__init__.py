"""APPLICATION FACTORY: builds the whole app."""
import os
from datetime import datetime

import click
from flask import Flask, flash, redirect, render_template, request

from app.extensions import csrf, db, login_manager, migrate
from config import config


def create_app(env="dev"):
    app = Flask(__name__)
    app.config.from_object(config[env])

    # Uploads folder: instance/uploads/ (outside static, private)
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, app.config["UPLOAD_SUBFOLDER"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 1. Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # 2. Models (so Flask-Migrate can "see" them)
    from app import models

    # 3. Blueprints. For a new module: import it and register it here.
    from app.auth import bp as auth_bp
    from app.categories import bp as categories_bp
    from app.main import bp as main_bp
    from app.permissions import bp as permissions_bp
    from app.products import bp as products_bp
    from app.profile import bp as profile_bp
    from app.roles import bp as roles_bp
    from app.users import bp as users_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(products_bp)

    # 4. Variables available in every template
    @app.context_processor
    def global_variables():
        return {"year": datetime.now().year, "app_name": app.config["APP_NAME"]}

    # 5. Error pages
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def file_too_large(error):
        flash("El archivo es demasiado grande (máximo 5 MB en total).", "danger")
        return redirect(request.referrer or "/")

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # 6. flask shell with db and models preloaded
    @app.shell_context_processor
    def shell_context():
        return {"db": db, "User": models.User, "Role": models.Role,
                "Permission": models.Permission, "Category": models.Category,
                "Product": models.Product}

    # 7. CLI COMMANDS
    @app.cli.command("seed")
    def seed():
        """Creates the base permissions, the admin and user roles, and links them.
        Safe to run many times: it never duplicates anything."""
        from app.permissions.catalog import BASE_PERMISSIONS, ROLE_PERMISSIONS

        # 1. Permissions
        for name, description in BASE_PERMISSIONS.items():
            if not db.session.scalar(db.select(models.Permission).filter_by(name=name)):
                db.session.add(models.Permission(name=name, description=description))
                click.echo(f"Permission '{name}' created.")
        db.session.flush()   # sends the INSERTs (no commit yet) so we can query them below

        # 2. Roles + their permissions
        for name, description in [
            ("admin", "Acceso total"),
            ("user", "Usuario normal: solo su panel y su perfil"),
        ]:
            role = db.session.scalar(db.select(models.Role).filter_by(name=name))
            if role is None:
                role = models.Role(name=name, description=description)
                db.session.add(role)
                click.echo(f"Role '{name}' created.")
            for permission_name in ROLE_PERMISSIONS[name]:
                permission = db.session.scalar(
                    db.select(models.Permission).filter_by(name=permission_name))
                if permission not in role.permissions:
                    role.permissions.append(permission)
            click.echo(f"Role '{name}': {len(role.permissions)} permission(s).")
        db.session.commit()

    @app.cli.command("create-user")
    @click.option("--name", prompt="Name")
    @click.option("--email", prompt="Email")
    @click.option("--role", prompt="Role", default="admin", show_default=True)
    @click.password_option(prompt="Password")
    def create_user(name, email, role, password):
        """Creates a user from the terminal (handy for the first admin)."""
        role_obj = db.session.scalar(db.select(models.Role).filter_by(name=role))
        if role_obj is None:
            click.echo(f"Role '{role}' does not exist. Run first: flask seed")
            return
        if db.session.scalar(db.select(models.User).filter_by(email=email.lower())):
            click.echo("A user with that email already exists.")
            return
        user = models.User(name=name, email=email.lower(), role=role_obj)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"User {email} created with role '{role}'.")

    return app
