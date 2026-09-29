"""FASTAPI APP (a separate API that reads/writes the SAME database as Flask).

Run (from the project folder, with the env active):
    uvicorn fastapi_app.main:app --reload --port 8001

Then open:
    http://127.0.0.1:8001/docs    -> interactive documentation (Swagger): test everything here
    http://127.0.0.1:8001/redoc   -> alternative documentation

Flask  = web pages (HTML) + its own JSON API in /api
FastAPI = only API, with automatic validation (Pydantic) and automatic docs
"""
from fastapi import FastAPI

from fastapi_app.routers import categories, products

app = FastAPI(
    title="FLSK API (FastAPI)",
    description="CRUD de categorías y productos sobre la misma base de datos de Flask.",
    version="1.0.0",
)

app.include_router(categories.router)
app.include_router(products.router)


@app.get("/", tags=["health"])
def health():
    """Quick check that the API is alive."""
    return {"status": "ok"}
