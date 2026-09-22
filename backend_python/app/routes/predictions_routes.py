"""
app/routes/predictions_routes.py
=================================
Prediction CRUD endpoints for DermisAI.

Endpoints
---------
POST   /api/predictions
    Dermatologist only.  Creates a stub Image row (no real file),
    then creates a Prediction row with AI-stubbed results.

GET    /api/predictions
    Dermatologist → own predictions only.
    Admin → all predictions.
    Supports ``limit`` and ``offset`` query params.

GET    /api/predictions/<prediction_id>
    Owner or admin.

PATCH  /api/predictions/<prediction_id>
    Dermatologist only.  Records clinician agreement.
"""

import random
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.image import Image
from app.models.patient import Patient
from app.models.prediction import Prediction

predictions_bp = Blueprint("predictions", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _forbidden():
    return jsonify({"success": False, "message": "Forbidden."}), 403


def _enrich(pred: Prediction) -> dict:
    """Return prediction.to_dict() enriched with patient demographics."""
    d = pred.to_dict()
    if pred.patient_id:
        pat = db.session.get(Patient, pred.patient_id)
        d["patient_age_group"] = pat.age_group if pat else None
        d["patient_skin_type"] = pat.skin_type if pat else None
    else:
        d["patient_age_group"] = None
        d["patient_skin_type"] = None
    return d


# ── POST /api/predictions ─────────────────────────────────────────────────────

@predictions_bp.post("")
@jwt_required()
def create_prediction():
    """Create a new AI-stubbed prediction.

    Roles
    -----
    dermatologist
        patient_id required in body.
    patient
        patient_id auto-resolved from the caller's linked Patient row.

    Request JSON
    ------------
    {
        "patient_id":      "uuid",   required for dermatologist, ignored for patient
        "location":        "...",    required  (stored in clinician_notes)
        "clinician_notes": "..."     optional
    }

    Responses
    ---------
    201  Prediction created.
    400  Validation error (missing fields, patient not found).
    403  Wrong role.
    500  Unexpected error.
    """
    claims = get_jwt()
    role   = claims.get("role")

    if role not in ("dermatologist", "patient"):
        return _forbidden()

    current_user_id = get_jwt_identity()
    hospital_id     = claims.get("hospital_id")

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be valid JSON."}), 400

    location    = body.get("location", "").strip()
    extra_notes = body.get("clinician_notes", "").strip()

    if not location:
        return jsonify({"success": False, "message": "location is required."}), 400

    # ── Resolve patient_id based on role ─────────────────────────────────────
    if role == "dermatologist":
        patient_id_raw = body.get("patient_id", "").strip()
        if not patient_id_raw:
            return jsonify({"success": False, "message": "patient_id is required."}), 400
        try:
            patient_uuid = uuid.UUID(patient_id_raw)
        except ValueError:
            return jsonify({"success": False, "message": "patient_id is not a valid UUID."}), 400
        patient = db.session.get(Patient, patient_uuid)
        if patient is None:
            return jsonify({"success": False, "message": "Patient not found."}), 400

    else:  # role == "patient"
        patient = Patient.query.filter_by(linked_user_id=current_user_id).first()
        if patient is None:
            return jsonify({
                "success": False,
                "message": "Your patient record is missing. Please contact support.",
            }), 400
        patient_uuid = patient.patient_id

    # ── Stub AI inference ─────────────────────────────────────────────────────
    is_cancer   = random.random() > 0.55
    probability = random.uniform(0.60, 0.98) if is_cancer else random.uniform(0.02, 0.30)
    confidence  = random.uniform(0.80, 0.98)
    result      = "cancer_detected" if is_cancer else "healthy"
    referral    = is_cancer and probability > 0.70
    proc_ms     = random.randint(1800, 2200)

    # Compose clinician_notes: prepend location so frontend can surface it
    notes_parts = ["Location: " + location]
    if extra_notes:
        notes_parts.append("Notes: " + extra_notes)
    composed_notes = " | ".join(notes_parts)

    try:
        # ── Insert stub Image row (required FK on predictions) ─────────────
        image = Image(
            file_path       = "uploads/demo/" + str(uuid.uuid4()) + ".jpg",
            file_hash       = uuid.uuid4().hex,
            file_size_bytes = 0,
            patient_id      = patient_uuid,
            hospital_id     = hospital_id,
            uploaded_by     = current_user_id,
        )
        db.session.add(image)
        db.session.flush()   # get image.image_id without committing yet

        # ── Insert Prediction row ──────────────────────────────────────────
        pred = Prediction(
            user_id              = current_user_id,
            patient_id           = patient_uuid,
            image_id             = image.image_id,
            hospital_id          = hospital_id,
            cancer_probability   = round(probability, 4),
            prediction           = result,
            confidence           = round(confidence, 4),
            referral_recommended = referral,
            processing_time_ms   = proc_ms,
            clinician_notes      = composed_notes,
            clinician_agreement  = None,
        )
        db.session.add(pred)

        # ── Bump patient prediction counter ────────────────────────────────
        if patient.total_predictions is None:
            patient.total_predictions = 1
        else:
            patient.total_predictions += 1

        # Update last_seen
        patient.last_seen = datetime.utcnow()
        if patient.first_seen is None:
            patient.first_seen = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "success":    True,
            "prediction": _enrich(pred),
            "location":   location,
        }), 201

    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to create prediction.",
            "detail":  str(exc),
        }), 500


# ── GET /api/predictions ──────────────────────────────────────────────────────

@predictions_bp.get("")
@jwt_required()
def list_predictions():
    """List predictions (own for doctor, all for admin, own for patient).

    Query params: limit (default 50), offset (default 0)

    Responses: 200 | 403 | 500
    """
    claims          = get_jwt()
    role            = claims.get("role")
    current_user_id = get_jwt_identity()

    if role not in ("dermatologist", "admin", "patient"):
        return _forbidden()

    try:
        limit  = min(int(request.args.get("limit",  50)), 200)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"success": False, "message": "limit and offset must be integers."}), 400

    try:
        query = db.select(Prediction).order_by(Prediction.detection_timestamp.desc())
        if role == "dermatologist":
            query = query.where(Prediction.user_id == current_user_id)
        elif role == "patient":
            # Patients see predictions linked to their own patient record
            patient = Patient.query.filter_by(linked_user_id=current_user_id).first()
            if patient is None:
                return jsonify({"success": True, "predictions": [], "total": 0}), 200
            query = query.where(Prediction.patient_id == patient.patient_id)

        count_query = db.select(db.func.count()).select_from(
            query.subquery()
        )
        total = db.session.execute(count_query).scalar() or 0

        rows = db.session.execute(
            query.limit(limit).offset(offset)
        ).scalars().all()

        return jsonify({
            "success":     True,
            "predictions": [_enrich(p) for p in rows],
            "total":       total,
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve predictions.",
            "detail":  str(exc),
        }), 500


# ── GET /api/predictions/<prediction_id> ─────────────────────────────────────

@predictions_bp.get("/<prediction_id>")
@jwt_required()
def get_prediction(prediction_id: str):
    """Retrieve a single prediction by ID.

    Accessible to the owning clinician or any admin.

    Responses: 200 | 403 | 404 | 500
    """
    claims          = get_jwt()
    role            = claims.get("role")
    current_user_id = get_jwt_identity()

    try:
        pred_uuid = uuid.UUID(prediction_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid prediction ID."}), 400

    pred = db.session.get(Prediction, pred_uuid)
    if pred is None:
        return jsonify({"success": False, "message": "Prediction not found."}), 404

    # Ownership check: admin sees all, doctor sees own, patient sees own via patient record
    if role == "admin":
        pass  # unrestricted
    elif role == "dermatologist":
        if str(pred.user_id) != current_user_id:
            return _forbidden()
    elif role == "patient":
        patient = Patient.query.filter_by(linked_user_id=current_user_id).first()
        if patient is None or str(pred.patient_id) != str(patient.patient_id):
            return _forbidden()
    else:
        return _forbidden()

    return jsonify({"success": True, "prediction": _enrich(pred)}), 200


# ── PATCH /api/predictions/<prediction_id> ────────────────────────────────────

@predictions_bp.patch("/<prediction_id>")
@jwt_required()
def update_prediction(prediction_id: str):
    """Record clinician agreement on a prediction.

    Requires role: dermatologist (and must own the prediction).

    Request JSON
    ------------
    { "agreement": true | false }

    Responses: 200 | 400 | 403 | 404 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "dermatologist":
        return _forbidden()

    current_user_id = get_jwt_identity()

    try:
        pred_uuid = uuid.UUID(prediction_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid prediction ID."}), 400

    pred = db.session.get(Prediction, pred_uuid)
    if pred is None:
        return jsonify({"success": False, "message": "Prediction not found."}), 404

    if str(pred.user_id) != current_user_id:
        return _forbidden()

    body = request.get_json(silent=True)
    if not body or "agreement" not in body:
        return jsonify({"success": False, "message": "agreement (true/false) is required."}), 400

    agreement_val = body["agreement"]
    if not isinstance(agreement_val, bool):
        return jsonify({"success": False, "message": "agreement must be a boolean."}), 400

    try:
        pred.clinician_agreement = "agree" if agreement_val else "disagree"
        db.session.commit()
        return jsonify({"success": True, "prediction": _enrich(pred)}), 200
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to update prediction.",
            "detail":  str(exc),
        }), 500
