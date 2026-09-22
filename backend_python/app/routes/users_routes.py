"""
app/routes/users_routes.py
===========================
User management endpoints for DermisAI.

Endpoints
---------
GET   /api/users           — list all users (admin only)
PATCH /api/users/<user_id> — toggle active flag (admin only)
"""

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from app.extensions import db
from app.models.user import User

users_bp = Blueprint("users", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _forbidden():
    return jsonify({"success": False, "message": "Forbidden."}), 403


# ── GET /api/users ────────────────────────────────────────────────────────────

@users_bp.get("")
@jwt_required()
def list_users():
    """Return all users ordered by registration date descending.

    Requires role: admin.
    Query params: limit (default 50), offset (default 0)

    Responses: 200 | 403 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "admin":
        return _forbidden()

    try:
        limit  = min(int(request.args.get("limit",  50)), 200)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"success": False, "message": "limit and offset must be integers."}), 400

    try:
        total = db.session.query(db.func.count(User.user_id)).scalar() or 0
        rows  = (
            User.query
            .order_by(User.date_registered.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return jsonify({
            "success": True,
            "users":   [u.to_dict() for u in rows],
            "total":   total,
        }), 200

    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": "Failed to retrieve users.",
            "detail":  str(exc),
        }), 500


# ── PATCH /api/users/<user_id> ────────────────────────────────────────────────

@users_bp.patch("/<user_id>")
@jwt_required()
def update_user(user_id: str):
    """Toggle a user's active status.

    Requires role: admin.

    Request JSON
    ------------
    { "active": true | false }

    Responses: 200 | 400 | 403 | 404 | 500
    """
    claims = get_jwt()
    if claims.get("role") != "admin":
        return _forbidden()

    try:
        u_uuid = uuid.UUID(user_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid user ID."}), 400

    user = db.session.get(User, u_uuid)
    if user is None:
        return jsonify({"success": False, "message": "User not found."}), 404

    body = request.get_json(silent=True)
    if not body or "active" not in body:
        return jsonify({"success": False, "message": "active (true/false) is required."}), 400

    active_val = body["active"]
    if not isinstance(active_val, bool):
        return jsonify({"success": False, "message": "active must be a boolean."}), 400

    try:
        user.active = active_val
        db.session.commit()
        return jsonify({"success": True, "user": user.to_dict()}), 200
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to update user.",
            "detail":  str(exc),
        }), 500
