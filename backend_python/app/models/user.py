"""
app/models/user.py
==================
SQLAlchemy model for the ``users`` table.

Password handling uses the ``bcrypt`` instance from app.extensions
so the same Bcrypt object that was initialised with the app is used
everywhere (avoids work-factor mismatches).
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import bcrypt, db


class User(db.Model):
    """Maps to the existing ``users`` table in skin_cancer_db."""

    __tablename__ = "users"

    # ── Columns ──────────────────────────────────────────────────────────────

    user_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
        comment="Auto-generated UUID primary key.",
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
    )

    # Never expose this field — to_dict() excludes it intentionally.
    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        comment="One of: admin, dermatologist, general_practitioner, nurse.",
    )

    full_name = db.Column(
        db.String(100),
        nullable=False,
    )

    phone = db.Column(
        db.String(20),
        nullable=True,
    )

    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False,
        index=True,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("TRUE"),
    )

    date_registered = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────

    # Many users → one hospital.
    hospital = db.relationship(
        "Hospital",
        back_populates="users",
        lazy="select",
    )

    # ── Password helpers ─────────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash ``password`` with bcrypt and store in ``password_hash``.

        Parameters
        ----------
        password : str
            Plain-text password provided by the user at registration / reset.
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Return ``True`` if ``password`` matches the stored hash.

        Parameters
        ----------
        password : str
            Plain-text password provided by the user at login.
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict.  ``password_hash`` is NEVER included."""
        return {
            "user_id":         str(self.user_id),
            "email":           self.email,
            "username":        self.username,
            "role":            self.role,
            "full_name":       self.full_name,
            "phone":           self.phone,
            "hospital_id":     str(self.hospital_id),
            "active":          self.active,
            "date_registered": self.date_registered.isoformat() if self.date_registered else None,
            "last_login":      self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return (
            f"<User id={self.user_id!s:.8}… "
            f"username={self.username!r} role={self.role!r}>"
        )
