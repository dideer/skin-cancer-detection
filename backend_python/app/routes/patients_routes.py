"""
app/routes/patients_routes.py
==============================
Patient record endpoints for DermisAI.

Endpoints
---------
GET    /api/patients        — list all patients (doctor or admin)
GET    /api/patients/me     — patient user's own scan record + predictions
GET    /api/patients/<id>   — single patient (doctor or admin)
POST   /api/patients        — create a new anonymous patient record (doctor only)
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.patient import Patient
from app.models.prediction import Prediction

patients_bp = Blueprint("patients", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _forbidden():
    return jsonify({"success": False, "message": "Forbidden."}), 403


def _patient_dict(p: Patient) -> dict:
    """Extend patient.to_dict() with linked_user_id."""
    d = p.to_dict()
    d["linked_user_id"] = str(p.linked_user_id) if p.linked_user_id else None
    return d


# ── GET /api/patients/me ──────────────────────────────────────────────────────
# Declared BEFORE /<patient_id> so Flask's router matches it first.

@patients_bp.get("/me")
@jwt_required()
def my_patient_record():
    """Return the Patient scan record linked to the calling user account.

    Requires role: patient.

    If no Patient row is linked yet, returns null patient with empty
    predictions list (the frontend renders an empty state).

    Responses: 200 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "patient":
        return _forbidden()

    current_user_id = get_jwt_identity()

    try:
        patient = Patient.query.filter_by(linked_user_id=current_user_id).first()

        if patient is None:
            return jsonify({
                "success":      True,
                "patient":      None,
                "predictions":  [],
                "appointments": [],
            }), 200

        preds = (
            Prediction.query
            .filter_by(patient_id=patient.patient_id)
            .order_by(Prediction.detection_timestamp.desc())
            .all()
        )

        # ── Appointments for this patient user ────────────────────────────
        from app.models.appointment import Appointment
        from app.models.user import User as UserModel

        raw_appts = (
            Appointment.query
            .filter_by(patient_user_id=current_user_id)
            .order_by(Appointment.requested_at.desc())
            .all()
        )

        def _enrich_appt(a):
            d = a.to_dict()
            doctor = db.session.get(UserModel, a.doctor_user_id) if a.doctor_user_id else None
            d["doctor_full_name"] = doctor.full_name if doctor else None
            if a.prediction_id:
                p = db.session.get(Prediction, a.prediction_id)
                d["prediction_summary"] = {
                    "prediction":          p.prediction         if p else None,
                    "confidence":          float(p.confidence)  if p and p.confidence is not None else None,
                    "cancer_probability":  float(p.cancer_probability) if p and p.cancer_probability is not None else None,
                    "detection_timestamp": p.detection_timestamp.isoformat() if p and p.detection_timestamp else None,
                } if p else None
            else:
                d["prediction_summary"] = None
            return d

        return jsonify({
            "success":      True,
            "patient":      _patient_dict(patient),
            "predictions":  [p.to_dict() for p in preds],
            "appointments": [_enrich_appt(a) for a in raw_appts],
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve patient record.",
            "detail":  str(exc),
        }), 500


# ── GET /api/patients ─────────────────────────────────────────────────────────

@patients_bp.get("")
@jwt_required()
def list_patients():
    """List all patient scan records.

    Accessible to dermatologist and admin.
    Query params: limit (default 50), offset (default 0)

    Responses: 200 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") not in ("dermatologist", "admin"):
        return _forbidden()

    try:
        limit  = min(int(request.args.get("limit",  50)), 200)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"success": False, "message": "limit and offset must be integers."}), 400

    try:
        total = db.session.query(db.func.count(Patient.patient_id)).scalar() or 0
        rows  = (
            Patient.query
            .order_by(Patient.last_seen.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return jsonify({
            "success":  True,
            "patients": [_patient_dict(p) for p in rows],
            "total":    total,
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve patients.",
            "detail":  str(exc),
        }), 500


# ── GET /api/patients/<patient_id> ────────────────────────────────────────────

@patients_bp.get("/<patient_id>")
@jwt_required()
def get_patient(patient_id: str):
    """Retrieve a single patient scan record by ID.

    Accessible to dermatologist and admin.

    Responses: 200 | 400 | 403 | 404 | 500
    """
    claims = get_jwt()
    if claims.get("role") not in ("dermatologist", "admin"):
        return _forbidden()

    try:
        p_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid patient ID."}), 400

    patient = db.session.get(Patient, p_uuid)
    if patient is None:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    return jsonify({"success": True, "patient": _patient_dict(patient)}), 200


# ── POST /api/patients ────────────────────────────────────────────────────────

@patients_bp.post("")
@jwt_required()
def create_patient():
    """Create a new anonymous patient scan record.

    Requires role: dermatologist.

    Request JSON
    ------------
    {
        "age_group":      "55-64",   optional
        "skin_type":      "III",     optional
        "linked_user_id": null       optional UUID
    }

    Responses: 201 | 400 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "dermatologist":
        return _forbidden()

    hospital_id = claims.get("hospital_id")
    body        = request.get_json(silent=True) or {}

    age_group      = body.get("age_group")
    skin_type      = body.get("skin_type")
    linked_raw     = body.get("linked_user_id")

    linked_user_id = None
    if linked_raw:
        try:
            linked_user_id = uuid.UUID(str(linked_raw))
        except ValueError:
            return jsonify({"success": False, "message": "linked_user_id is not a valid UUID."}), 400

    try:
        patient = Patient(
            patient_id_hash = uuid.uuid4().hex,
            age_group       = age_group or None,
            skin_type       = skin_type or None,
            hospital_id     = hospital_id,
            first_seen      = datetime.utcnow(),
            last_seen       = datetime.utcnow(),
            total_predictions = 0,
            linked_user_id  = linked_user_id,
        )
        db.session.add(patient)
        db.session.commit()

        return jsonify({"success": True, "patient": _patient_dict(patient)}), 201

    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to create patient.",
            "detail":  str(exc),
        }), 500
