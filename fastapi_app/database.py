"""DATABASE CONNECTION for FastAPI (plain SQLAlchemy, without Flask).

FastAPI has no "Flask-SQLAlchemy": you build the 3 pieces yourself:
  engine        -> the connection to the DB (same DATABASE_URL as Flask, from .env)
  SessionLocal  -> a "factory" of sessions (one per request)
  get_db()      -> dependency: opens a session, gives it to the route, and ALWAYS closes it
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent of every FastAPI model (the equivalent of db.Model)."""


def get_db():
    db = SessionLocal()
    try:
        yield db          # the route uses it...
    finally:
        db.close()        # ...and it's closed even if there was an error
