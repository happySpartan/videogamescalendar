"""Videogame Calendar backend.

A single installable python package that serves the public game/release API
(``app.api``), the token-gated admin API (``app.admin``) and the Celery data
sync worker + scheduler (``app.sync``). The SQLAlchemy models live in
``app.models`` and DB/session helpers in ``app.db``.

Run the API:
    uvicorn app.main:app --port 8000

Run the worker and beat (from repo root, with this package installed):
    celery -A app.sync.celery_app worker --loglevel=info
    celery -A app.sync.celery_app beat   --loglevel=info
"""
