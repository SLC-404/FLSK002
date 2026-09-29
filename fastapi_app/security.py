"""API KEY as a dependency: every route that "depends" on it requires the X-API-Key header."""
import os

from fastapi import Header, HTTPException, status


def api_key_required(x_api_key: str | None = Header(default=None)):
    # Header(...) reads the "X-API-Key" header (FastAPI converts x_api_key -> X-Api-Key)
    expected = os.getenv("API_KEY", "")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key inválida o faltante")
