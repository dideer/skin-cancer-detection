"""
app/models/prediction.py
========================
SQLAlchemy model for the ``predictions`` table.

Columns confirmed by inspecting the live skin_cancer_db schema:
  prediction_id, user_id, patient_id, image_id, hospital_id,
  cancer_probability, prediction, confidence, referral_recommended,
  processing_time_ms, clinician_notes, clinician_agreement,
  detection_timestamp
"""

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Prediction(db.Model):
    """Maps to the existing ``predictions`` table in skin_cancer_db."""

    __tablename__ = "predictions"

    prediction_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
    )

    # FK to users.user_id  — the clinician who submitted the prediction
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    patient_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("patients.patient_id"),
        nullable=True,
    )

    image_id = db.Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("hospitals.hospital_id"),
        nullable=True,
    )

    cancer_probability  = db.Column(db.Numeric(5, 4), nullable=True)
    prediction          = db.Column(db.String(50),    nullable=True)
    confidence          = db.Column(db.Numeric(5, 4), nullable=True)

    # True = model flagged for referral
    referral_recommended = db.Column(db.Boolean, nullable=True, default=False)

    processing_time_ms = db.Column(db.Integer, nullable=True)
    clinician_notes    = db.Column(db.Text,    nullable=True)

    # NULL = not yet reviewed; 'agree' / 'disagree' once reviewed
    clinician_agreement = db.Column(db.String(20), nullable=True)

    detection_timestamp = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    def to_dict(self) -> dict:
        return {
            "prediction_id":       str(self.prediction_id),
            "user_id":             str(self.user_id),
            "patient_id":          str(self.patient_id)  if self.patient_id  else None,
            "hospital_id":         str(self.hospital_id) if self.hospital_id else None,
            "cancer_probability":  float(self.cancer_probability) if self.cancer_probability is not None else None,
            "prediction":          self.prediction,
            "confidence":          float(self.confidence) if self.confidence is not None else None,
            "referral_recommended": self.referral_recommended,
            "processing_time_ms":  self.processing_time_ms,
            "clinician_notes":     self.clinician_notes,
            "clinician_agreement": self.clinician_agreement,
            "detection_timestamp": self.detection_timestamp.isoformat() if self.detection_timestamp else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.prediction_id!s:.8}… "
            f"result={self.prediction!r}>"
        )
