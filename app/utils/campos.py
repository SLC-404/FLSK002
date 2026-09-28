"""CAMPOS DE ARCHIVO REUTILIZABLES (los usan el perfil y el CRUD de usuarios)."""
from flask_wtf.file import FileAllowed, FileField, FileSize

MB = 1024 * 1024


def campo_foto():
    return FileField("Foto de perfil", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Solo imágenes JPG, PNG o WEBP"),
        FileSize(max_size=2 * MB, message="La foto debe pesar máximo 2 MB"),
    ])


def campo_identificacion():
    return FileField("Identificación (INE, pasaporte...)", validators=[
        FileAllowed(["pdf", "jpg", "jpeg", "png"], "Solo PDF, JPG o PNG"),
        FileSize(max_size=3 * MB, message="El archivo debe pesar máximo 3 MB"),
    ])
