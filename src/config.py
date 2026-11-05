"""Project paths and tunable defaults."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"
MODEL_DIR = ROOT / "models"
DOCS_DIR = ROOT / "docs"

MODEL_PATH = MODEL_DIR / "sign_model.joblib"
SETTINGS_PATH = MODEL_DIR / "settings.json"
CASCADE_PATH = ROOT / "haarcascade_frontalface_default.xml"

# Capture and recognition
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30
SMOOTH_WINDOW = 9
COMMIT_HOLD_SECONDS = 1.5
MIN_CONFIDENCE = 0.55
MAX_TEXT_LENGTH = 180

# The hand should live inside this normalised box. The face detector still
# runs on the whole frame so skin outside the crop can never win the contour.
ROI = (0.47, 0.04, 0.99, 0.98)

# Feature contract. Bump the version whenever the vector changes.
FEATURE_VERSION = "shape-v1"
FEATURE_DIM = 61
FOURIER_BINS = 20
RADIAL_BINS = 24
CONTOUR_POINTS = 64

# Dataset rules
MIN_CLASSES = 2
MIN_SAMPLES_PER_CLASS = 10
MIN_TOTAL_SAMPLES = 40
DEFAULT_COLLECT_COUNT = 80

# Skin ranges are deliberately broad. The workbench exposes these in the lab.
SKIN_PRESETS: dict[str, dict[str, list[int]]] = {
    "daylight": {
        "label": "Daylight",
        "lower": [0, 28, 48],
        "upper": [22, 175, 255],
    },
    "indoor": {
        "label": "Room light",
        "lower": [0, 26, 34],
        "upper": [26, 195, 255],
    },
    "lowlight": {
        "label": "Low light",
        "lower": [0, 36, 22],
        "upper": [29, 220, 240],
    },
}

DEFAULT_SKIN_PRESET = "indoor"

# Nice, restrained colours in BGR for the OpenCV overlay.
INK_BGR = (26, 24, 22)
PAPER_BGR = (228, 238, 242)
ACCENT_BGR = (44, 80, 226)
GREEN_BGR = (79, 107, 46)
MUTED_BGR = (145, 141, 132)
