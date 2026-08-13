"""
Production WSGI entry point. Use with a WSGI server, e.g.:

    gunicorn wsgi:app

`run.py` remains the entry point for local development (`python run.py`),
since it also enables Flask's debug/reload server.
"""

from app import create_app

app = create_app()
