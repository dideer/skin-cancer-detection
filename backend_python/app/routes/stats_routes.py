"""
app/routes/stats_routes.py
===========================
Statistics endpoints for the three role-based dashboards.

All endpoints require a valid JWT (Bearer token).  Each endpoint
performs an inline role check against the ``role`` claim embedded
in the token; no decorator is used per the task spec.

Endpoints
---------
GET /api/stats/admin
    Admin only.  System-wide counts: users, predictions, patients,
    hospitals.

GET /api/stats/doctor
    Dermatologist only.  Per-doctor counts scoped to the calling
    user's user_id: today's predictions, all predictions, pending
    reviews (clinician_agreement IS NULL), referrals flagged.

GET /api/stats/patient
    Patient role only.  Returns zeros for now because the schema does
    not yet link a ``users`` row (role='patient') to a ``patients``
    row.  The frontend will render an empty state.
"""

from datetime import datetime, time

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.hospital import Hospital
from app.models.patient import Patient
from app.models.prediction import Prediction
from app.models.user import User

stats_bp = Blueprint("stats", __name__)


# ── GET /api/stats/admin ──────────────────────────────────────────────────────

@stats_bp.get("/admin")
@jwt_required()
def admin_stats():
    """System-wide counts for the admin dashboard.

    Role required: admin
    Responses: 200 with stats dict | 401 missing/invalid token | 403 wrong role | 500
    """
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"success": False, "message": "Forbidden."}), 403

    try:
        total_users       = db.session.query(db.func.count(User.user_id)).scalar()
        total_predictions = db.session.query(db.func.count(Prediction.prediction_id)).scalar()
        total_patients    = db.session.query(db.func.count(Patient.patient_id)).scalar()
        total_hospitals   = db.session.query(db.func.count(Hospital.hospital_id)).scalar()

        return jsonify({
            "success": True,
            "stats": {
                "total_users":       total_users       or 0,
                "total_predictions": total_predictions or 0,
                "total_patients":    total_patients    or 0,
                "total_hospitals":   total_hospitals   or 0,
            },
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve admin stats.",
            "detail":  str(exc),
        }), 500


# ── GET /api/stats/doctor ─────────────────────────────────────────────────────

@stats_bp.get("/doctor")
@jwt_required()
def doctor_stats():
    """Per-doctor statistics for the dermatologist dashboard.

    All counts are scoped to the calling user's user_id so doctors
    only see their own numbers.

    Role required: dermatologist
    Responses: 200 with stats dict | 401 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "dermatologist":
        return jsonify({"success": False, "message": "Forbidden."}), 403

    # get_jwt_identity() returns the string UUID stored as the JWT sub claim
    current_user_id = get_jwt_identity()

    # Confirm the user still exists in the DB
    user = db.session.get(User, current_user_id)
    if user is None:
        return jsonify({"success": False, "message": "User not found."}), 401

    try:
        # Start of today in UTC
        today_start = datetime.combine(datetime.utcnow().date(), time.min)

        # Predictions submitted today by this doctor
        predictions_today = (
            db.session.query(db.func.count(Prediction.prediction_id))
            .filter(
                Prediction.user_id == current_user_id,
                Prediction.detection_timestamp >= today_start,
            )
            .scalar()
        )

        # All predictions by this doctor
        total_predictions = (
            db.session.query(db.func.count(Prediction.prediction_id))
            .filter(Prediction.user_id == current_user_id)
            .scalar()
        )

        # Predictions not yet reviewed (clinician_agreement IS NULL)
        pending_reviews = (
            db.session.query(db.func.count(Prediction.prediction_id))
            .filter(
                Prediction.user_id == current_user_id,
                Prediction.clinician_agreement.is_(None),
            )
            .scalar()
        )

        # Predictions where the model flagged a referral
        referrals_flagged = (
            db.session.query(db.func.count(Prediction.prediction_id))
            .filter(
                Prediction.user_id == current_user_id,
                Prediction.referral_recommended.is_(True),
            )
            .scalar()
        )

        return jsonify({
            "success": True,
            "stats": {
                "predictions_today": predictions_today or 0,
                "total_predictions": total_predictions or 0,
                "pending_reviews":   pending_reviews   or 0,
                "referrals_flagged": referrals_flagged or 0,
            },
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve doctor stats.",
            "detail":  str(exc),
        }), 500


# ── GET /api/stats/patient ────────────────────────────────────────────────────

@stats_bp.get("/patient")
@jwt_required()
def patient_stats():
    """Stub stats for the patient dashboard.

    The schema does not yet link a ``users`` row (role='patient') to a
    ``patients`` scan record, so all counts are zero.  The frontend
    renders an empty/placeholder state.

    Role required: patient
    Responses: 200 with zero stats | 401 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "patient":
        return jsonify({"success": False, "message": "Forbidden."}), 403

    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if user is None:
        return jsonify({"success": False, "message": "User not found."}), 401

    # Returning zeros until the users↔patients link is implemented.
    return jsonify({
        "success": True,
        "stats": {
            "my_scans":    0,
            "last_result": None,
            "pending":     0,
        },
    }), 200
