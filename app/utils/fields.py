"""REUSABLE FILE FIELDS (used by the profile and the users CRUD)."""
from flask_wtf.file import FileAllowed, FileField, FileSize

MB = 1024 * 1024


def photo_field():
    return FileField("Foto de perfil", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Solo imágenes JPG, PNG o WEBP"),
        FileSize(max_size=2 * MB, message="La foto debe pesar máximo 2 MB"),
    ])


def id_document_field():
    return FileField("Identificación (INE, pasaporte...)", validators=[
        FileAllowed(["pdf", "jpg", "jpeg", "png"], "Solo PDF, JPG o PNG"),
        FileSize(max_size=3 * MB, message="El archivo debe pesar máximo 3 MB"),
    ])
