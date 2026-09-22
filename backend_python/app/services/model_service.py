"""
app/services/model_service.py
==============================
Loads the DermisAI TFLite models (skin detector + cancer detector)
and provides a simple predict() function.

Models are downloaded from Google Drive on first run if not already
present in app/services/ml_models/.
"""

import os
import time
import gdown
import numpy as np
import tensorflow as tf
from PIL import Image

# ── Paths ────────────────────────────────────────────────────────────────────
# __file__ = backend_python/app/services/model_service.py
#   dirname → .../app/services
#   dirname → .../app
BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, "ml_models")
os.makedirs(MODELS_DIR, exist_ok=True)

STAGE1_PATH = os.path.join(MODELS_DIR, "stage1_skin_detector.tflite")
CANCER_PATH = os.path.join(MODELS_DIR, "cancer_detector.tflite")

# ── Google Drive File IDs ────────────────────────────────────────────────────
STAGE1_DRIVE_ID = "1g3sB1-dqHwLCNvG927ebwupPo4X3R18k"
CANCER_DRIVE_ID = "1w0CmHHo3qlq3a_ikcf2t3ialeB01N3Ps"

# ── Image settings ───────────────────────────────────────────────────────────
IMG_SIZE = (224, 224)

# ── Loaded interpreters (set at startup) ─────────────────────────────────────
_stage1_interpreter = None
_cancer_interpreter = None


# ── Download helpers ─────────────────────────────────────────────────────────
def _download_if_missing(path: str, drive_id: str, label: str) -> None:
    """Download file from Google Drive if it doesn't exist locally."""
    if os.path.exists(path):
        print(f"[INFO] {label} already exists at {path}")
        return
    print(f"[INFO] Downloading {label} from Google Drive...")
    try:
        gdown.download(id=drive_id, output=path, quiet=False)
        print(f"[INFO] {label} downloaded.")
    except Exception as exc:
        print(f"[ERROR] Could not download {label}: {exc}")


# ── Load models at import time ───────────────────────────────────────────────
def _load_models() -> None:
    """Download (if needed) and load both TFLite interpreters."""
    global _stage1_interpreter, _cancer_interpreter

    # --- Stage 1: skin detector ---
    _download_if_missing(STAGE1_PATH, STAGE1_DRIVE_ID, "Stage 1 (skin detector)")
    try:
        _stage1_interpreter = tf.lite.Interpreter(model_path=STAGE1_PATH)
        _stage1_interpreter.allocate_tensors()
        print("[INFO] Stage 1 model loaded.")
    except Exception as exc:
        print(f"[ERROR] Failed to load Stage 1 model: {exc}")
        _stage1_interpreter = None

    # --- Stage 3: cancer detector ---
    _download_if_missing(CANCER_PATH, CANCER_DRIVE_ID, "Stage 3 (cancer detector)")
    try:
        _cancer_interpreter = tf.lite.Interpreter(model_path=CANCER_PATH)
        _cancer_interpreter.allocate_tensors()
        print("[INFO] Stage 3 model loaded.")
    except Exception as exc:
        print(f"[ERROR] Failed to load Stage 3 model: {exc}")
        _cancer_interpreter = None


# ── Image preprocessing ──────────────────────────────────────────────────────
def _preprocess(image_path: str) -> np.ndarray:
    """Load image, resize to 224x224, return float32 array (1, 224, 224, 3)."""
    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32)
    return np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)


# ── Individual model runners ─────────────────────────────────────────────────
def _run_stage1(img_array: np.ndarray) -> float:
    """Return raw sigmoid output for Stage 1 (skin detector)."""
    inp = _stage1_interpreter.get_input_details()
    out = _stage1_interpreter.get_output_details()
    _stage1_interpreter.set_tensor(inp[0]["index"], img_array)
    _stage1_interpreter.invoke()
    return float(_stage1_interpreter.get_tensor(out[0]["index"])[0][0])


def _run_cancer(img_array: np.ndarray) -> float:
    """Return raw sigmoid output for Stage 3 (cancer detector)."""
    inp = _cancer_interpreter.get_input_details()
    out = _cancer_interpreter.get_output_details()
    _cancer_interpreter.set_tensor(inp[0]["index"], img_array)
    _cancer_interpreter.invoke()
    return float(_cancer_interpreter.get_tensor(out[0]["index"])[0][0])


# ── Public API ───────────────────────────────────────────────────────────────
def predict(image_path: str) -> dict:
    """
    Run the full 2-stage pipeline on an image.

    Returns
    -------
    dict with keys:
        success              : bool
        is_skin              : bool
        skin_confidence      : float (0.0 – 1.0)
        prediction           : "cancer_detected" | "healthy" | "not_skin" | "error"
        cancer_probability   : float (0.0 – 1.0)   — 0 if not skin
        confidence           : float (0.0 – 1.0)
        referral_recommended : bool
        processing_time_ms   : int
        message              : str (only on error)
    """
    start = time.time()

    # ── Sanity check ─────────────────────────────────────────────────────
    if _stage1_interpreter is None or _cancer_interpreter is None:
        return {
            "success": False,
            "message": "Models are not loaded.",
        }

    # ── Preprocess ───────────────────────────────────────────────────────
    try:
        img_array = _preprocess(image_path)
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to read image: {exc}",
        }

    # ── Stage 1: skin check ──────────────────────────────────────────────
    skin_raw = _run_stage1(img_array)
    # Classes: ['not_skin', 'skin'] → sigmoid > 0.5 means skin
    is_skin        = skin_raw > 0.5
    skin_conf      = skin_raw if is_skin else (1.0 - skin_raw)

    if not is_skin:
        return {
            "success":              True,
            "is_skin":              False,
            "skin_confidence":      round(skin_conf, 4),
            "prediction":           "not_skin",
            "cancer_probability":   0.0,
            "confidence":           round(skin_conf, 4),
            "referral_recommended": False,
            "processing_time_ms":   int((time.time() - start) * 1000),
        }

    # ── Stage 3: cancer check ────────────────────────────────────────────
    cancer_raw = _run_cancer(img_array)
    # Classes: ['cancer', 'not_cancer'] → sigmoid > 0.5 means not_cancer
    has_cancer       = cancer_raw <= 0.5
    cancer_prob      = (1.0 - cancer_raw) if has_cancer else (1.0 - cancer_raw)
    # Actually cancer_probability should always be the "probability of cancer"
    cancer_prob      = 1.0 - cancer_raw
    conf             = cancer_raw if not has_cancer else (1.0 - cancer_raw)

    return {
        "success":              True,
        "is_skin":              True,
        "skin_confidence":      round(skin_conf, 4),
        "prediction":           "cancer_detected" if has_cancer else "healthy",
        "cancer_probability":   round(cancer_prob, 4),
        "confidence":           round(conf, 4),
        "referral_recommended": has_cancer and cancer_prob > 0.70,
        "processing_time_ms":   int((time.time() - start) * 1000),
    }


# ── Run at import ────────────────────────────────────────────────────────────
_load_models()