"""Punto de entrada: "flask run" lee FLASK_APP=run.py y usa esta variable "app"."""
from app import create_app

app = create_app("dev")
