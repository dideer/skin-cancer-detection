"""
app/models/hospital.py
======================
SQLAlchemy model for the ``hospitals`` table.

The table is already created in PostgreSQL — this class maps to it
without generating any DDL.  Do NOT run ``flask db migrate`` for
this model; use ``flask db stamp head`` if you later initialise
Flask-Migrate against the existing schema.
"""

from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Hospital(db.Model):
    """Maps to the existing ``hospitals`` table in skin_cancer_db."""

    __tablename__ = "hospitals"

    # ── Columns ──────────────────────────────────────────────────────────────

    hospital_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
        comment="Auto-generated UUID primary key.",
    )

    hospital_name = db.Column(
        db.String(255),
        nullable=False,
    )

    country = db.Column(
        db.String(100),
        nullable=False,
    )

    city = db.Column(
        db.String(100),
        nullable=False,
    )

    contact_info = db.Column(
        db.String(255),
        nullable=True,
    )

    timezone = db.Column(
        db.String(50),
        nullable=True,
    )

    capabilities = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    # ── Relationships ────────────────────────────────────────────────────────

    # One hospital → many users.
    # ``lazy="select"`` means the related rows are loaded on first access
    # (standard behaviour; change to "dynamic" or "selectin" as needed).
    users = db.relationship(
        "User",
        back_populates="hospital",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of the hospital."""
        return {
            "hospital_id":  str(self.hospital_id),
            "hospital_name": self.hospital_name,
            "country":      self.country,
            "city":         self.city,
            "contact_info": self.contact_info,
            "timezone":     self.timezone,
            "capabilities": self.capabilities,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Hospital id={self.hospital_id!s:.8}… "
            f"name={self.hospital_name!r} city={self.city!r}>"
        )
