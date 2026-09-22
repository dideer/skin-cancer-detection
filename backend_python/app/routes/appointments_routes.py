"""
app/routes/appointments_routes.py
==================================
Appointment management endpoints for DermisAI.

Endpoints
---------
POST  /api/appointments
    Patient only.  Request a consultation appointment linked to a
    scan result (prediction_id).

GET   /api/appointments
    Patient → own appointments.
    Dermatologist → all appointments (pending queue + own history).
    Admin → all appointments.
    Enriched with patient name/email, doctor name, prediction summary.

PATCH /api/appointments/<appointment_id>
    Dermatologist only.  Approve or deny a pending appointment.
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.prediction import Prediction
from app.models.user import User

appointments_bp = Blueprint("appointments", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _forbidden():
    return jsonify({"success": False, "message": "Forbidden."}), 403


def _enrich_appointment(appt: Appointment) -> dict:
    """Return appointment.to_dict() with joined user + prediction fields."""
    d = appt.to_dict()

    # Patient user details
    patient_user = db.session.get(User, appt.patient_user_id)
    d["patient_full_name"] = patient_user.full_name if patient_user else None
    d["patient_email"]     = patient_user.email     if patient_user else None

    # Doctor user details (may be None until assigned)
    doctor_user = db.session.get(User, appt.doctor_user_id) if appt.doctor_user_id else None
    d["doctor_full_name"]  = doctor_user.full_name if doctor_user else None

    # Prediction summary
    if appt.prediction_id:
        pred = db.session.get(Prediction, appt.prediction_id)
        d["prediction_summary"] = {
            "prediction":          pred.prediction         if pred else None,
            "confidence":          float(pred.confidence)  if pred and pred.confidence is not None else None,
            "cancer_probability":  float(pred.cancer_probability) if pred and pred.cancer_probability is not None else None,
            "detection_timestamp": pred.detection_timestamp.isoformat() if pred and pred.detection_timestamp else None,
        } if pred else None
    else:
        d["prediction_summary"] = None

    return d


# ── POST /api/appointments ────────────────────────────────────────────────────

@appointments_bp.post("")
@jwt_required()
def create_appointment():
    """Request a consultation appointment.

    Requires role: patient.

    Request JSON
    ------------
    {
        "prediction_id": "uuid",   required
        "patient_notes": "..."     optional
    }

    Responses
    ---------
    201  Appointment created.
    400  Validation error or prediction not found.
    403  Wrong role, or prediction does not belong to this patient.
    409  Duplicate pending appointment for same prediction.
    500  Unexpected error.
    """
    claims = get_jwt()
    if claims.get("role") != "patient":
        return _forbidden()

    current_user_id = get_jwt_identity()

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be valid JSON."}), 400

    pred_id_raw    = (body.get("prediction_id") or "").strip()
    patient_notes  = (body.get("patient_notes") or "").strip() or None

    if not pred_id_raw:
        return jsonify({"success": False, "message": "prediction_id is required."}), 400

    # Parse prediction UUID
    try:
        pred_uuid = uuid.UUID(pred_id_raw)
    except ValueError:
        return jsonify({"success": False, "message": "prediction_id is not a valid UUID."}), 400

    # Confirm prediction exists
    pred = db.session.get(Prediction, pred_uuid)
    if pred is None:
        return jsonify({"success": False, "message": "Prediction not found."}), 400

    # Confirm the prediction belongs to this patient's linked record
    patient = Patient.query.filter_by(linked_user_id=current_user_id).first()
    if patient is None or str(pred.patient_id) != str(patient.patient_id):
        return jsonify({
            "success": False,
            "message": "You are not authorised to request an appointment for this scan.",
        }), 403

    # Prevent duplicate pending requests
    existing = Appointment.query.filter_by(
        patient_user_id=current_user_id,
        prediction_id=pred_uuid,
        status="pending",
    ).first()
    if existing:
        return jsonify({
            "success": False,
            "message": "You already have a pending request for this scan.",
        }), 409

    try:
        appt = Appointment(
            patient_user_id = current_user_id,
            prediction_id   = pred_uuid,
            doctor_user_id  = None,
            status          = "pending",
            patient_notes   = patient_notes,
        )
        db.session.add(appt)
        db.session.commit()

        return jsonify({
            "success":     True,
            "appointment": _enrich_appointment(appt),
        }), 201

    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to create appointment.",
            "detail":  str(exc),
        }), 500


# ── GET /api/appointments ─────────────────────────────────────────────────────

@appointments_bp.get("")
@jwt_required()
def list_appointments():
    """List appointments, scoped by role.

    - patient      → own appointments only
    - dermatologist → all appointments (to see pending queue)
    - admin        → all appointments

    Query params: limit (default 50), offset (default 0)

    Responses: 200 | 403 | 500
    """
    claims          = get_jwt()
    role            = claims.get("role")
    current_user_id = get_jwt_identity()

    if role not in ("patient", "dermatologist", "admin"):
        return _forbidden()

    try:
        limit  = min(int(request.args.get("limit",  50)), 200)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"success": False, "message": "limit and offset must be integers."}), 400

    try:
        query = db.select(Appointment).order_by(Appointment.requested_at.desc())

        if role == "patient":
            query = query.where(Appointment.patient_user_id == current_user_id)
        # dermatologist and admin see all — no additional filter

        count_q = db.select(db.func.count()).select_from(query.subquery())
        total   = db.session.execute(count_q).scalar() or 0

        rows = db.session.execute(
            query.limit(limit).offset(offset)
        ).scalars().all()

        return jsonify({
            "success":      True,
            "appointments": [_enrich_appointment(a) for a in rows],
            "total":        total,
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve appointments.",
            "detail":  str(exc),
        }), 500


# ── PATCH /api/appointments/<appointment_id> ──────────────────────────────────

@appointments_bp.patch("/<appointment_id>")
@jwt_required()
def respond_to_appointment(appointment_id: str):
    """Approve or deny a pending appointment request.

    Requires role: dermatologist.

    Request JSON
    ------------
    {
        "action":       "approve" | "deny",
        "doctor_notes": "..."    optional
    }

    Responses: 200 | 400 | 403 | 404 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "dermatologist":
        return _forbidden()

    current_user_id = get_jwt_identity()

    try:
        appt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid appointment ID."}), 400

    appt = db.session.get(Appointment, appt_uuid)
    if appt is None:
        return jsonify({"success": False, "message": "Appointment not found."}), 404

    if appt.status != "pending":
        return jsonify({
            "success": False,
            "message": "This appointment has already been responded to (status: " + appt.status + ").",
        }), 400

    body = request.get_json(silent=True)
    if not body or "action" not in body:
        return jsonify({"success": False, "message": "action ('approve' or 'deny') is required."}), 400

    action = body["action"].strip().lower()
    if action not in ("approve", "deny"):
        return jsonify({"success": False, "message": "action must be 'approve' or 'deny'."}), 400

    doctor_notes = (body.get("doctor_notes") or "").strip() or None

    try:
        appt.status         = "approved" if action == "approve" else "denied"
        appt.doctor_user_id = current_user_id
        appt.responded_at   = datetime.utcnow()
        appt.doctor_notes   = doctor_notes

        db.session.commit()

        return jsonify({
            "success":     True,
            "appointment": _enrich_appointment(appt),
        }), 200

    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to update appointment.",
            "detail":  str(exc),
        }), 500
