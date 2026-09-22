"""
wsgi.py
=======
WSGI entry point for production servers (Gunicorn, uWSGI, etc.).

Usage with Gunicorn:
    gunicorn "wsgi:app" --bind 0.0.0.0:5000 --workers 4

The ``app`` object exposed here is what the WSGI server loads.
Do NOT set debug=True here; use the DevelopmentConfig only locally.
"""

from app import create_app

app = create_app()
