"""
app/extensions.py
=================
Instantiate Flask extensions here WITHOUT binding them to an app.

Each extension is initialised with ``ext.init_app(app)`` inside
the application factory (``create_app``).  This pattern lets the
same extension objects be imported anywhere in the package without
causing circular imports.
"""

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# ── Database ORM ─────────────────────────────────────────────────────────────
db = SQLAlchemy()

# ── Schema migrations ────────────────────────────────────────────────────────
migrate = Migrate()

# ── Password hashing ─────────────────────────────────────────────────────────
bcrypt = Bcrypt()

# ── JSON Web Tokens ──────────────────────────────────────────────────────────
jwt = JWTManager()

# ── Cross-Origin Resource Sharing ────────────────────────────────────────────
cors = CORS()
