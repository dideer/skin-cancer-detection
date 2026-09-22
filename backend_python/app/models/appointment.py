"""
app/models/appointment.py
=========================
SQLAlchemy model for the ``appointments`` table.

Schema:
  appointment_id    UUID PK
  patient_user_id   UUID FK → users.user_id   NOT NULL
  prediction_id     UUID FK → predictions.prediction_id  nullable
  doctor_user_id    UUID FK → users.user_id   nullable (assigned on approve/deny)
  status            VARCHAR(20) NOT NULL DEFAULT 'pending'
  requested_at      TIMESTAMP
  responded_at      TIMESTAMP  nullable
  patient_notes     TEXT  nullable
  doctor_notes      TEXT  nullable
"""

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Appointment(db.Model):
    """Maps to the existing ``appointments`` table in skin_cancer_db."""

    __tablename__ = "appointments"

    appointment_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
    )

    # The user (role='patient') who requested the appointment
    patient_user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    # Optional link to a specific prediction / scan
    prediction_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("predictions.prediction_id"),
        nullable=True,
    )

    # The doctor who responds; NULL until approved/denied
    doctor_user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id"),
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    requested_at = db.Column(
        db.DateTime,
        nullable=True,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    responded_at  = db.Column(db.DateTime, nullable=True)
    patient_notes = db.Column(db.Text,     nullable=True)
    doctor_notes  = db.Column(db.Text,     nullable=True)

    def to_dict(self) -> dict:
        return {
            "appointment_id":  str(self.appointment_id),
            "patient_user_id": str(self.patient_user_id),
            "prediction_id":   str(self.prediction_id)   if self.prediction_id  else None,
            "doctor_user_id":  str(self.doctor_user_id)  if self.doctor_user_id else None,
            "status":          self.status,
            "requested_at":    self.requested_at.isoformat()  if self.requested_at  else None,
            "responded_at":    self.responded_at.isoformat()  if self.responded_at  else None,
            "patient_notes":   self.patient_notes,
            "doctor_notes":    self.doctor_notes,
        }

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.appointment_id!s:.8}… "
            f"status={self.status!r}>"
        )
