"""Uvicorn entrypoint: `uvicorn app.main:app --reload`."""

from app.bootstrap import create_app

app = create_app()
