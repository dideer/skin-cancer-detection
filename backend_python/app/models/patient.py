"""
app/models/patient.py
=====================
SQLAlchemy model for the ``patients`` table.

This table stores anonymous patient scan records — it is NOT the same
as a ``users`` row with role='patient'.  Columns confirmed by inspecting
the live skin_cancer_db schema.
"""

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Patient(db.Model):
    """Maps to the existing ``patients`` table in skin_cancer_db."""

    __tablename__ = "patients"

    patient_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
    )

    patient_id_hash = db.Column(db.String(255), nullable=True)

    age_group = db.Column(db.String(50),  nullable=True)
    skin_type = db.Column(db.String(10),  nullable=True)

    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("hospitals.hospital_id"),
        nullable=True,
    )

    first_seen = db.Column(db.DateTime, nullable=True)
    last_seen  = db.Column(db.DateTime, nullable=True)

    total_predictions = db.Column(db.Integer, nullable=True, default=0)

    # Nullable FK linking this anonymous scan record to a users row with
    # role='patient', set at self-registration.
    linked_user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id"),
        nullable=True,
        index=True,
    )

    def to_dict(self) -> dict:
        return {
            "patient_id":        str(self.patient_id),
            "age_group":         self.age_group,
            "skin_type":         self.skin_type,
            "hospital_id":       str(self.hospital_id)      if self.hospital_id      else None,
            "first_seen":        self.first_seen.isoformat() if self.first_seen       else None,
            "last_seen":         self.last_seen.isoformat()  if self.last_seen        else None,
            "total_predictions": self.total_predictions,
            "linked_user_id":    str(self.linked_user_id)   if self.linked_user_id   else None,
        }

    def __repr__(self) -> str:
        return f"<Patient id={self.patient_id!s:.8}…>"
