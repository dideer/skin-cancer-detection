"""
run.py
======
Development runner — starts the Flask dev server with debug mode.

Usage:
    python run.py

Do NOT use this in production.  Use wsgi.py with Gunicorn instead.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",   # accessible on the local network (handy for testing)
        port=5000,
        debug=True,        # auto-reload on code changes, verbose tracebacks
    )
