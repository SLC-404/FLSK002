"""MANEJO DE ARCHIVOS SUBIDOS.

Reglas de seguridad:
  1. Nunca se usa el nombre que manda el usuario: se genera uno aleatorio (uuid).
  2. Los archivos se guardan FUERA de static/ (en instance/uploads/),
     así nadie los abre con un link directo: se sirven por una ruta con permisos.
  3. La extensión se valida en el formulario (FileAllowed) y el tamaño (FileSize).
"""
import os
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def se_subio(campo):
    """¿El usuario SÍ eligió un archivo en este campo?

    Ojo: al editar con Form(obj=usuario), WTForms precarga el campo con lo que
    hay en la BD (un texto, el nombre del archivo). Por eso no basta con
    "if campo.data": hay que revisar que sea un archivo de verdad (FileStorage).
    """
    return isinstance(campo.data, FileStorage) and bool(campo.data.filename)


def carpeta(tipo):
    """Ruta absoluta de la carpeta de un tipo de archivo: 'fotos' o 'identificaciones'."""
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], tipo)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def guardar_archivo(archivo, tipo):
    """Guarda el archivo con un nombre único y regresa ese nombre (para la BD)."""
    extension = os.path.splitext(secure_filename(archivo.filename))[1].lower()   # ".png"
    nombre = f"{uuid.uuid4().hex}{extension}"                                     # "3f2a...9c.png"
    archivo.save(os.path.join(carpeta(tipo), nombre))
    return nombre


def borrar_archivo(nombre, tipo):
    """Borra un archivo si existe (al reemplazarlo o al eliminar al usuario)."""
    if nombre:
        ruta = os.path.join(carpeta(tipo), nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
