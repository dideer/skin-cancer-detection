"""
app/routes/auth.py
==================
Authentication blueprint for DermisAI.

Endpoints
---------
POST /api/auth/login
    Authenticate with email + password.
    Returns a signed JWT access token and the user's public profile.

GET /api/auth/me
    Return the profile of the currently authenticated user.
    Requires a valid Bearer token in the Authorization header.

POST /api/auth/logout
    Stateless logout — instructs the client to discard the token.
    Requires a valid Bearer token in the Authorization header.
    (Token blocklisting can be added here later via JTI storage.)
"""

from datetime import datetime
import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@auth_bp.post("/login")
def login():
    """Authenticate a user and return a JWT access token.

    Request JSON
    ------------
    {
        "email":    "clinician@hospital.org",
        "password": "secret"
    }

    Responses
    ---------
    200  Login successful — token + user profile returned.
    400  Missing / malformed request body or missing fields.
    401  Invalid credentials (email not found OR wrong password).
    403  Account is deactivated.
    500  Unexpected server error.
    """
    try:
        # ── 1. Parse body ─────────────────────────────────────────────────
        body = request.get_json(silent=True)

        if body is None:
            return jsonify({
                "success": False,
                "message": "Request body must be valid JSON.",
            }), 400

        email    = body.get("email")
        password = body.get("password")

        # ── 2. Validate fields ────────────────────────────────────────────
        errors = {}
        if not email or not isinstance(email, str) or not email.strip():
            errors["email"] = "email is required and must be a non-empty string."
        if not password or not isinstance(password, str) or not password.strip():
            errors["password"] = "password is required and must be a non-empty string."

        if errors:
            return jsonify({
                "success": False,
                "message": "Validation failed.",
                "errors":  errors,
            }), 400

        # ── 3. Look up user (case-insensitive email) ──────────────────────
        user = User.query.filter_by(email=email.strip().lower()).first()

        # 401 — same message for "not found" and "wrong password" to prevent
        # user-enumeration attacks.
        if user is None or not user.check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid email or password.",
            }), 401

        # ── 4. Account status check ───────────────────────────────────────
        if not user.active:
            return jsonify({
                "success": False,
                "message": "Account is deactivated.",
            }), 403

        # ── 5. Record last login ──────────────────────────────────────────
        user.last_login = datetime.utcnow()
        db.session.commit()

        # ── 6. Issue JWT ──────────────────────────────────────────────────
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                "role":        user.role,
                "hospital_id": str(user.hospital_id),
            },
        )

        return jsonify({
            "success":      True,
            "access_token": access_token,
            "user":         user.to_dict(),
        }), 200

    except Exception as exc:  # noqa: BLE001
        # Roll back any partial write before responding.
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred. Please try again.",
            "detail":  str(exc),          # strip in production if desired
        }), 500


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@auth_bp.get("/me")
@jwt_required()
def me():
    """Return the profile of the currently authenticated user.

    The JWT sub claim holds the user's UUID string (set at login).

    Responses
    ---------
    200  User profile returned.
    404  User record no longer exists (e.g. deleted after token was issued).
    """
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({
            "success": False,
            "message": "User not found.",
        }), 404

    return jsonify({
        "success": True,
        "user":    user.to_dict(),
    }), 200


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@auth_bp.post("/logout")
@jwt_required()
def logout():
    """Stateless logout — instructs the client to discard the token.

    Because JWTs are self-contained, the server cannot truly invalidate
    a token without a blocklist.  Add JTI-based blocklisting here when
    that feature is required.

    Responses
    ---------
    200  Logout acknowledged.
    """
    return jsonify({
        "success": True,
        "message": "Logged out.",
    }), 200


# ── POST /api/auth/register ───────────────────────────────────────────────────

@auth_bp.post("/register")
def register():
    """Create a new user account (dermatologist or patient only).

    Request JSON
    ------------
    {
        "email":     "...",
        "username":  "...",
        "password":  "...",
        "full_name": "...",
        "phone":     "...",   (optional)
        "role":      "dermatologist" | "patient"
    }

    Responses
    ---------
    201  Account created — user profile returned (no auto-login).
    400  Validation error or forbidden role.
    409  Email or username already registered.
    500  Unexpected server error.
    """
    # ── Avoid circular import — email_validator is a top-level package ────
    from email_validator import EmailNotValidError, validate_email

    # Default hospital assigned to every self-registered user.
    DEFAULT_HOSPITAL_ID = "6a1bf619-0c7b-409f-8b9e-ca93c0cdeb38"
    ALLOWED_ROLES = {"dermatologist", "patient"}

    try:
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({"success": False, "message": "Request body must be valid JSON."}), 400

        # ── Required field presence ───────────────────────────────────────
        required = ["email", "username", "password", "full_name", "role"]
        for field in required:
            val = body.get(field)
            if not val or not isinstance(val, str) or not val.strip():
                return jsonify({
                    "success": False,
                    "message": field + " is required and must be a non-empty string.",
                }), 400

        email     = body["email"].strip().lower()
        username  = body["username"].strip()
        password  = body["password"]
        full_name = body["full_name"].strip()
        role      = body["role"].strip().lower()
        phone     = body.get("phone", "").strip() or None

        # ── Email format ──────────────────────────────────────────────────
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            return jsonify({"success": False, "message": "Invalid email address: " + str(e)}), 400

        # ── Password length ───────────────────────────────────────────────
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

        # ── Role allowlist ────────────────────────────────────────────────
        if role not in ALLOWED_ROLES:
            return jsonify({
                "success": False,
                "message": "Role must be 'dermatologist' or 'patient'. "
                           "Admin accounts cannot be self-registered.",
            }), 400

        # ── Uniqueness checks ─────────────────────────────────────────────
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "Email already registered."}), 409

        if User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "Username already taken."}), 409

        # ── Create user ───────────────────────────────────────────────────
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            role=role,
            phone=phone,
            hospital_id=DEFAULT_HOSPITAL_ID,
            active=True,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # ── If registering as a patient, create a linked Patient scan record ──
        if role == "patient":
            from app.models.patient import Patient
            patient = Patient(
                patient_id_hash   = uuid.uuid4().hex,
                hospital_id       = DEFAULT_HOSPITAL_ID,
                linked_user_id    = user.user_id,
                age_group         = None,
                skin_type         = None,
                total_predictions = 0,
            )
            db.session.add(patient)
            db.session.commit()

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "user":    user.to_dict(),
        }), 201

    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred. Please try again.",
            "detail":  str(exc),
        }), 500
