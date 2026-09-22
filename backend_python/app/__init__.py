"""
app/__init__.py
===============
Application factory for DermisAI Flask backend.

Usage:
    from app import create_app
    app = create_app()          # uses FLASK_ENV from environment
    app = create_app("testing") # override for tests
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify

# Load .env before anything else so os.environ is populated
# when config.py reads from it.
load_dotenv()

from app.config import config_by_name, default_config
from app.extensions import bcrypt, cors, db, jwt, migrate


def create_app(env: str | None = None) -> Flask:
    """
    Create, configure, and return the Flask application.

    Parameters
    ----------
    env : str | None
        One of ``"development"``, ``"production"``, or ``"testing"``.
        Falls back to the ``FLASK_ENV`` environment variable, then
        ``DevelopmentConfig`` if neither is set.
    """
    app = Flask(__name__, instance_relative_config=False)

    # ── 1. Load configuration ─────────────────────────────────────────────
    env = env or os.environ.get("FLASK_ENV", "development")
    cfg = config_by_name.get(env, default_config)
    app.config.from_object(cfg)

    # ── 2. Initialise extensions ──────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # CORS: allow origins defined in config, apply to all /api/* routes
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # ── 3. Register blueprints ────────────────────────────────────────────
    _register_blueprints(app)

    # ── 4. Frontend static file routes ───────────────────────────────────────
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    _pages_dir    = os.path.join(_project_root, "frontend", "pages")
    _css_dir      = os.path.join(_project_root, "frontend", "css")

    from flask import redirect, send_from_directory

    @app.route("/")
    @app.route("/pages/")
    def serve_index():
        """Redirect root to the login page."""
        return redirect("/pages/index.html")

    @app.route("/pages/<path:filename>")
    def serve_frontend(filename):
        """Serve any HTML (or other) file from frontend/pages/."""
        return send_from_directory(_pages_dir, filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        """Serve any file from frontend/css/."""
        return send_from_directory(_css_dir, filename)

    # ── 5. Built-in API routes ────────────────────────────────────────────
    @app.get("/api/health")
    def health_check():
        """Health-check endpoint."""
        return jsonify({"status": "ok"}), 200

    # ── 5b. DEBUG endpoint — database diagnostics (temporary) ────────────
    @app.get("/api/debug-db")
    def debug_db():
        """Diagnostic endpoint: shows DB connection status + tables."""
        from app.extensions import db
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                current_db   = conn.execute(text("SELECT current_database()")).scalar()
                current_user = conn.execute(text("SELECT current_user")).scalar()
                pg_version   = conn.execute(text("SELECT version()")).scalar()
                tables = conn.execute(text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname='public' ORDER BY tablename"
                )).fetchall()
            return jsonify({
                "status":       "ok",
                "database":     current_db,
                "db_user":      current_user,
                "pg_version":   pg_version.split(",")[0],
                "tables":       [t[0] for t in tables],
                "table_count":  len(tables),
                "database_url": app.config["SQLALCHEMY_DATABASE_URI"][:40] + "...",
            })
        except Exception as e:
            return jsonify({
                "status":        "error",
                "error_type":    type(e).__name__,
                "error_message": str(e),
                "database_url":  app.config["SQLALCHEMY_DATABASE_URI"][:40] + "...",
            }), 500

    # ── 6. JSON error handlers ───────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "The requested URL does not exist"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "method_not_allowed", "message": str(e)}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "internal_server_error", "message": "An unexpected error occurred"}), 500

    # ── 7. Shell context ──────────────────────────────────────────────────
    @app.shell_context_processor
    def make_shell_context():
        """Inject db and common models into `flask shell` automatically."""
        return {"db": db}

    return app


# ── Private helpers ───────────────────────────────────────────────────────────

def _register_blueprints(app: Flask) -> None:
    """
    Central place to register all route blueprints.
    Add new blueprints here as the API grows.
    """
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.hospital_routes import hospital_bp
    app.register_blueprint(hospital_bp, url_prefix="/api/hospitals")

    from app.routes.stats_routes import stats_bp
    app.register_blueprint(stats_bp, url_prefix="/api/stats")

    from app.routes.predictions_routes import predictions_bp
    app.register_blueprint(predictions_bp, url_prefix="/api/predictions")

    from app.routes.patients_routes import patients_bp
    app.register_blueprint(patients_bp, url_prefix="/api/patients")

    from app.routes.users_routes import users_bp
    app.register_blueprint(users_bp, url_prefix="/api/users")

    from app.routes.appointments_routes import appointments_bp
    app.register_blueprint(appointments_bp, url_prefix="/api/appointments")