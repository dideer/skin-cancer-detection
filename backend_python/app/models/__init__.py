"""
app/models/__init__.py
======================
Re-export all models so Flask-Migrate can detect them and so that
other modules can import cleanly with ``from app.models import User``.
"""

from app.models.appointment import Appointment
from app.models.hospital import Hospital
from app.models.image import Image
from app.models.patient import Patient
from app.models.prediction import Prediction
from app.models.user import User
