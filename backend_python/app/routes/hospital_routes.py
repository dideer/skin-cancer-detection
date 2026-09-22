"""
app/routes/hospital_routes.py
==============================
Public endpoints for hospital data.

Endpoints
---------
GET /api/hospitals
    No authentication required.
    Returns the list of all registered hospitals (id, name, city).
"""

from flask import Blueprint, jsonify

from app.extensions import db
from app.models.hospital import Hospital

hospital_bp = Blueprint("hospitals", __name__)


@hospital_bp.get("")
def list_hospitals():
    """Return all hospitals as a lightweight list.

    Responses
    ---------
    200  { "success": true, "hospitals": [ { hospital_id, hospital_name, city }, ... ] }
    500  Unexpected server error.
    """
    try:
        hospitals = db.session.execute(
            db.select(Hospital).order_by(Hospital.hospital_name)
        ).scalars().all()

        return jsonify({
            "success":   True,
            "hospitals": [
                {
                    "hospital_id":   str(h.hospital_id),
                    "hospital_name": h.hospital_name,
                    "city":          h.city,
                }
                for h in hospitals
            ],
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve hospitals.",
            "detail":  str(exc),
        }), 500
