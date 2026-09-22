"""
seed_user.py
============
One-off script — inserts a single test user into the ``users`` table.

Idempotent: running it a second time prints a notice and exits cleanly
without creating a duplicate row.

Usage (with venv active, from backend_python/):
    python seed_user.py

Override the target hospital:
    $env:HOSPITAL_ID = "your-uuid-here"; python seed_user.py
"""

import os

from app import create_app
from app.extensions import db
from app.models import User

# ── Configuration ─────────────────────────────────────────────────────────────
# Default to the known hospital UUID; override via environment variable.
HOSPITAL_ID = os.environ.get(
    "HOSPITAL_ID",
    "6a1bf619-0c7b-409f-8b9e-ca93c0cdeb38",
)

# ── Seed ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        email = "s.okonkwo@cityhospital.org"

        existing = User.query.filter_by(email=email).first()

        if existing:
            print(f"User already exists: {existing.email}")
        else:
            user = User(
                email=email,
                username="sokonkwo",
                full_name="Dr. Sarah Okonkwo",
                role="dermatologist",
                phone=None,
                hospital_id=HOSPITAL_ID,
                active=True,
            )
            user.set_password("demo1234")

            db.session.add(user)
            db.session.commit()

            print(f"Created user: {user.email}")
            print(f"  user_id    : {user.user_id}")
            print(f"  role       : {user.role}")
            print(f"  hospital_id: {user.hospital_id}")
            print(f"  password   : demo1234  (bcrypt-hashed in DB)")
