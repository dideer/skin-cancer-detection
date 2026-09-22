"""
check.py
========
DermisAI — pre-flight verification script.

Runs every connectivity check and prints a ✓ / ✗ summary you can
screenshot before moving on to models.

Usage (with venv active):
    python check.py

No new dependencies — only what is already in requirements.txt.
"""

import importlib
import os
import re
import sys

# ── Colour helpers (works in Windows Terminal / PowerShell 7) ─────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

PASS = f"{GREEN}  ✓{RESET}"
FAIL = f"{RED}  ✗{RESET}"


def ok(label: str, detail: str = "") -> None:
    print(f"{PASS}  {label}" + (f"  →  {detail}" if detail else ""))


def fail(label: str, detail: str = "", hint: str = "") -> None:
    print(f"{FAIL}  {label}" + (f"  →  {RED}{detail}{RESET}" if detail else ""))
    if hint:
        print(f"      {YELLOW}hint:{RESET} {hint}")


def section(title: str) -> None:
    print(f"\n{YELLOW}{'─' * 60}{RESET}")
    print(f"{YELLOW}  {title}{RESET}")
    print(f"{YELLOW}{'─' * 60}{RESET}")


results: list[bool] = []


def check(passed: bool, label: str, detail: str = "", hint: str = "") -> bool:
    results.append(passed)
    if passed:
        ok(label, detail)
    else:
        fail(label, detail, hint)
    return passed


# ══════════════════════════════════════════════════════════════════════════════
# 1. Python environment
# ══════════════════════════════════════════════════════════════════════════════
section("1 · Python environment")

# 1a. Running inside the venv?
in_venv = sys.prefix != sys.base_prefix
check(
    in_venv,
    "Running inside a virtual environment",
    sys.prefix if in_venv else "",
    "Run:  venv\\Scripts\\activate",
)

# 1b. Python version
major, minor = sys.version_info.major, sys.version_info.minor
py_ok = major == 3 and minor >= 11
check(
    py_ok,
    f"Python version ≥ 3.11",
    f"{sys.version.split()[0]}",
    "Install Python 3.11+ and recreate the venv.",
)

# 1c. Pinned packages installed at correct versions
REQUIRED = {
    "flask":               "3.0.3",
    "flask_sqlalchemy":    "3.1.1",
    "flask_migrate":       "4.0.7",
    "psycopg2":            "2.9",      # binary; version prefix match
    "flask_bcrypt":        "1.0.1",
    "flask_jwt_extended":  "4.6.0",
    "flask_cors":          "4.0.1",
    "dotenv":              "1.0.1",    # python-dotenv
    "marshmallow":         "3.21.3",
    "email_validator":     "2.1.1",
}

# importlib.metadata maps distribution names; we check what we can import
import importlib.metadata as meta

pkg_map = {
    "flask":              "Flask",
    "flask_sqlalchemy":   "Flask-SQLAlchemy",
    "flask_migrate":      "Flask-Migrate",
    "psycopg2":           "psycopg2-binary",
    "flask_bcrypt":       "Flask-Bcrypt",
    "flask_jwt_extended": "Flask-JWT-Extended",
    "flask_cors":         "Flask-Cors",
    "dotenv":             "python-dotenv",
    "marshmallow":        "marshmallow",
    "email_validator":    "email-validator",
}

for mod, dist in pkg_map.items():
    expected = REQUIRED[mod]
    try:
        installed = meta.version(dist)
        match = installed.startswith(expected)
        check(match, f"  {dist}", f"{installed}", f"pip install {dist}=={expected}")
    except meta.PackageNotFoundError:
        check(False, f"  {dist}", "NOT INSTALLED", f"pip install {dist}=={expected}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Environment file (.env)
# ══════════════════════════════════════════════════════════════════════════════
section("2 · Environment file (.env)")

env_path = os.path.join(os.path.dirname(__file__), ".env")
check(
    os.path.isfile(env_path),
    ".env file exists",
    env_path,
    "Copy .env.example to .env and fill in your values.",
)

# Load it
from dotenv import load_dotenv
load_dotenv(env_path, override=True)

for key in ("FLASK_ENV", "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL", "CORS_ORIGINS"):
    val = os.environ.get(key, "")
    check(
        bool(val),
        f"  {key} is set",
        val if key not in ("SECRET_KEY", "JWT_SECRET_KEY")
             else f"{val[:6]}… (masked)",
        f"Add {key}=<value> to your .env",
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3. Flask app boot + config sanity
# ══════════════════════════════════════════════════════════════════════════════
section("3 · Flask app boot & config")

app = None
try:
    from app import create_app
    app = create_app()
    check(True, "create_app() succeeded")
except Exception as exc:
    check(False, "create_app() failed", str(exc), "Check app/__init__.py for import errors.")

if app:
    with app.app_context():
        # Config class
        env_name = os.environ.get("FLASK_ENV", "development")
        cfg_name = type(app.config.__class__).__name__
        # We stored the class directly, not an instance — read DEBUG as proxy
        is_dev = app.config.get("DEBUG") and not app.config.get("TESTING")
        check(True, f"  FLASK_ENV", env_name)

        # DATABASE_URL (mask password)
        db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        masked = re.sub(r"(:)([^:@]+)(@)", r"\1****\3", db_url)
        check(bool(db_url), "  SQLALCHEMY_DATABASE_URI", masked)

        # JWT_ACCESS_TOKEN_EXPIRES
        jwt_exp = app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
        check(jwt_exp is not False, "  JWT_ACCESS_TOKEN_EXPIRES", str(jwt_exp))

        # CORS_ORIGINS
        origins = app.config.get("CORS_ORIGINS", [])
        check(
            bool(origins),
            "  CORS_ORIGINS",
            ", ".join(origins) if origins else "EMPTY",
            "Set CORS_ORIGINS in .env",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. Database connectivity (no table creation)
# ══════════════════════════════════════════════════════════════════════════════
section("4 · Database connectivity")

if app:
    from app.extensions import db
    from sqlalchemy import text

    with app.app_context():
        # 4a. Raw connection
        try:
            with db.engine.connect() as conn:
                pg_version = conn.execute(text("SELECT version()")).scalar()
                current_db = conn.execute(text("SELECT current_database()")).scalar()

            check(True, "PostgreSQL connection established")
            check(True, "  pg version",  pg_version.split(",")[0])
            check(True, "  database",    current_db)

            # 4b. Confirm it is the right DB
            check(
                current_db == "skin_cancer_db",
                "  Connected to skin_cancer_db",
                current_db,
                "Update DATABASE_URL in .env to point to skin_cancer_db.",
            )

        except Exception as exc:
            msg = str(exc).splitlines()[0]
            check(False, "PostgreSQL connection failed", msg)
            # Diagnose common errors
            if "Connection refused" in msg or "could not connect" in msg.lower():
                print(f"      {YELLOW}hint:{RESET} PostgreSQL is not running or the port is wrong.")
                print(f"             Start it:  pg_ctl start  or check Services → postgresql-x64-17")
            elif "password authentication" in msg.lower():
                print(f"      {YELLOW}hint:{RESET} Wrong password. Update DATABASE_URL in .env.")
            elif "does not exist" in msg.lower():
                print(f"      {YELLOW}hint:{RESET} Database not found.")
                print(f"             Create it:  psql -U postgres -c \"CREATE DATABASE skin_cancer_db;\"")
else:
    check(False, "Skipped — app failed to boot")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Route registration
# ══════════════════════════════════════════════════════════════════════════════
section("5 · Route registration")

if app:
    rules = {r.rule for r in app.url_map.iter_rules()}

    check("/api/health"    in rules, "  /api/health registered")
    check("/api/auth/ping" in rules, "  /api/auth/ping registered")

    # Confirm 404 handler returns JSON (not HTML)
    with app.test_client() as client:
        r = client.get("/api/nonexistent")
        is_json = r.content_type.startswith("application/json")
        check(
            r.status_code == 404 and is_json,
            "  /api/nonexistent → JSON 404",
            f"{r.status_code} {r.content_type}",
            "Add a JSON @app.errorhandler(404) in create_app().",
        )

        # Health check
        r = client.get("/api/health")
        check(
            r.status_code == 200,
            "  GET /api/health → 200",
            r.get_data(as_text=True).strip(),
        )

        # Auth ping
        r = client.get("/api/auth/ping")
        check(
            r.status_code == 200,
            "  GET /api/auth/ping → 200",
            r.get_data(as_text=True).strip(),
        )
else:
    check(False, "Skipped — app failed to boot")


# ══════════════════════════════════════════════════════════════════════════════
# 6. CORS headers (simulated preflight)
# ══════════════════════════════════════════════════════════════════════════════
section("6 · CORS headers")

if app:
    with app.test_client() as client:
        # Simulate browser preflight from http://127.0.0.1:5500
        r = client.options(
            "/api/health",
            headers={
                "Origin": "http://127.0.0.1:5500",
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        acac = r.headers.get("Access-Control-Allow-Credentials", "")

        check(
            "127.0.0.1:5500" in acao or acao == "*",
            "  Access-Control-Allow-Origin set",
            acao or "(missing)",
            "Check CORS_ORIGINS in .env and cors.init_app() in create_app().",
        )
        check(
            acac.lower() == "true",
            "  Access-Control-Allow-Credentials: true",
            acac or "(missing)",
            "Pass supports_credentials=True to cors.init_app().",
        )
else:
    check(False, "Skipped — app failed to boot")


# ══════════════════════════════════════════════════════════════════════════════
# Final summary
# ══════════════════════════════════════════════════════════════════════════════
total  = len(results)
passed = sum(results)
failed = total - passed

print(f"\n{'═' * 60}")
if failed == 0:
    print(f"{GREEN}  ALL {total} CHECKS PASSED — ready to move on to models ✓{RESET}")
else:
    print(f"{RED}  {failed} / {total} CHECKS FAILED — fix the issues above before continuing ✗{RESET}")
print(f"{'═' * 60}\n")

sys.exit(0 if failed == 0 else 1)
