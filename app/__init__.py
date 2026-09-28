"""APPLICATION FACTORY: arma la aplicación completa."""
import os
from datetime import datetime

import click
from flask import Flask, flash, redirect, render_template, request

from app.extensions import csrf, db, login_manager, migrate
from config import config


def create_app(entorno="dev"):
    app = Flask(__name__)
    app.config.from_object(config[entorno])

    # Carpeta de archivos subidos: instance/uploads/ (fuera de static, privada)
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, app.config["UPLOAD_SUBCARPETA"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 1. Extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # 2. Modelos (para que Flask-Migrate los "vea")
    from app import models

    # 3. Blueprints. Para un módulo nuevo: impórtalo y regístralo aquí.
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.perfil import bp as perfil_bp
    from app.roles import bp as roles_bp
    from app.usuarios import bp as usuarios_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(roles_bp)

    # 4. Variables disponibles en todas las plantillas
    @app.context_processor
    def variables_globales():
        return {"anio": datetime.now().year, "nombre_app": app.config["NOMBRE_APP"]}

    # 5. Páginas de error
    @app.errorhandler(403)
    def prohibido(error):
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(error):
        return render_template("errores/404.html"), 404

    @app.errorhandler(413)
    def archivo_muy_grande(error):
        flash("El archivo es demasiado grande (máximo 5 MB en total).", "danger")
        return redirect(request.referrer or "/")

    @app.errorhandler(500)
    def error_servidor(error):
        db.session.rollback()
        return render_template("errores/500.html"), 500

    # 6. flask shell con db y modelos cargados
    @app.shell_context_processor
    def contexto_shell():
        return {"db": db, "Usuario": models.Usuario, "Rol": models.Rol}

    # 7. COMANDOS DE TERMINAL
    @app.cli.command("seed")
    def seed():
        """Crea los roles básicos: admin y usuario (no duplica si ya existen)."""
        for nombre, descripcion in [
            ("admin", "Acceso total: administra usuarios y roles"),
            ("usuario", "Usuario normal: solo su perfil"),
        ]:
            if not db.session.scalar(db.select(models.Rol).filter_by(nombre=nombre)):
                db.session.add(models.Rol(nombre=nombre, descripcion=descripcion))
                click.echo(f"Rol '{nombre}' creado.")
        db.session.commit()

    @app.cli.command("crear-usuario")
    @click.option("--nombre", prompt="Nombre")
    @click.option("--email", prompt="Correo")
    @click.option("--rol", prompt="Rol", default="admin", show_default=True)
    @click.password_option(prompt="Contraseña")
    def crear_usuario(nombre, email, rol, password):
        """Crea un usuario desde la terminal (útil para el primer admin)."""
        rol_obj = db.session.scalar(db.select(models.Rol).filter_by(nombre=rol))
        if rol_obj is None:
            click.echo(f"No existe el rol '{rol}'. Corre primero: flask seed")
            return
        if db.session.scalar(db.select(models.Usuario).filter_by(email=email.lower())):
            click.echo("Ya existe un usuario con ese correo.")
            return
        usuario = models.Usuario(nombre=nombre, email=email.lower(), rol=rol_obj)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuario {email} creado con rol '{rol}'.")

    return app
