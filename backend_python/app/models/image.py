"""
app/models/image.py
===================
SQLAlchemy model for the ``images`` table.

Columns confirmed from live skin_cancer_db schema:
  image_id, file_path, file_hash, file_size_bytes, patient_id,
  hospital_id, uploaded_by, blur_score, brightness_score,
  contrast_score, uploaded_timestamp
"""

from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Image(db.Model):
    """Maps to the existing ``images`` table in skin_cancer_db."""

    __tablename__ = "images"

    image_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=db.text("gen_random_uuid()"),
    )

    file_path = db.Column(db.String(255), unique=True, nullable=False)
    file_hash = db.Column(db.String(255), unique=True, nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)

    patient_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("patients.patient_id"),
        nullable=False,
        index=True,
    )

    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False,
    )

    # FK to users.user_id — the clinician who uploaded the image
    uploaded_by = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id"),
        nullable=False,
    )

    # Quality metrics (0.00 – 1.00)
    blur_score       = db.Column(db.Numeric(3, 2), nullable=True)
    brightness_score = db.Column(db.Numeric(3, 2), nullable=True)
    contrast_score   = db.Column(db.Numeric(3, 2), nullable=True)

    uploaded_timestamp = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    def to_dict(self) -> dict:
        return {
            "image_id":          str(self.image_id),
            "file_path":         self.file_path,
            "file_hash":         self.file_hash,
            "file_size_bytes":   self.file_size_bytes,
            "patient_id":        str(self.patient_id),
            "hospital_id":       str(self.hospital_id),
            "uploaded_by":       str(self.uploaded_by),
            "blur_score":        float(self.blur_score)       if self.blur_score       is not None else None,
            "brightness_score":  float(self.brightness_score) if self.brightness_score is not None else None,
            "contrast_score":    float(self.contrast_score)   if self.contrast_score   is not None else None,
            "uploaded_timestamp": self.uploaded_timestamp.isoformat() if self.uploaded_timestamp else None,
        }

    def __repr__(self) -> str:
        return f"<Image id={self.image_id!s:.8}… path={self.file_path!r}>"
