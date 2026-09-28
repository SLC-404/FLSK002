"""UPLOADED FILES.

Security rules:
  1. Never use the name the user sends: a random one (uuid) is generated.
  2. Files are stored OUTSIDE static/ (in instance/uploads/), so nobody can open
     them with a direct link: they are served by a route that checks permissions.
  3. Extension is validated in the form (FileAllowed) and so is size (FileSize).
"""
import os
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def was_uploaded(field):
    """Did the user actually choose a file in this field?

    Careful: when editing with Form(obj=user), WTForms preloads the field with the
    value in the DB (a string, the file name). So "if field.data" is not enough:
    we must check it is a real file (FileStorage).
    """
    return isinstance(field.data, FileStorage) and bool(field.data.filename)


def folder(kind):
    """Absolute path of the folder for a kind of file: 'photos' or 'id_documents'."""
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], kind)
    os.makedirs(path, exist_ok=True)
    return path


def save_file(file, kind):
    """Saves the file with a unique name and returns that name (for the DB)."""
    extension = os.path.splitext(secure_filename(file.filename))[1].lower()   # ".png"
    name = f"{uuid.uuid4().hex}{extension}"                                   # "3f2a...9c.png"
    file.save(os.path.join(folder(kind), name))
    return name


def delete_file(name, kind):
    """Deletes a file if it exists (when replacing it or deleting the user)."""
    if name:
        path = os.path.join(folder(kind), name)
        if os.path.exists(path):
            os.remove(path)
