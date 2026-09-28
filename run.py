"""Entry point.

- Development:  "flask run" reads FLASK_APP=run.py (.flaskenv) and uses this "app" variable.
- Production:   gunicorn run:app  (Mac/Linux)   or   waitress-serve run:app  (Windows)

APP_ENV in .env picks the config class: dev (default) or prod.
"""
import os

from app import create_app

app = create_app(os.getenv("APP_ENV", "dev"))
