"""Shared constants and measured values used across the report."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
FIG = ROOT / "figures"

DATA = json.loads((ROOT / "model_metrics.json").read_text(encoding="utf-8"))

LABELS: list[str] = DATA["labels"]
SAMPLES: int = DATA["samples"]
ACCURACY: float = DATA["accuracy"]
TRAIN_ACCURACY: float = DATA["train_accuracy"]
TEST_SAMPLES: int = DATA["test_samples"]
CLASS_COUNTS: dict[str, int] = DATA["class_counts"]
PER_CLASS: dict[str, dict] = DATA["metrics"]["per_class"]
MACRO_F1: float = DATA["metrics"]["macro_f1"]
WEIGHTED_F1: float = DATA["metrics"]["weighted_f1"]

STUDENT = "Samarth Vegada"
ENROLMENT = "[Enrollment Number]"
MENTOR = "[Name of Faculty Mentor]"
DEGREE = "Bachelor of Technology"
BRANCH = "CSE (AI\u2013ML)"
DEPARTMENT = "Department of CSE (AI\u2013ML)"
FACULTY = "Faculty of Engineering Sciences and Technology"
UNIVERSITY = "Adani University, Ahmedabad \u2013 382421, India"
MONTH = "November 2026"

TITLE = "PALM / SIGN"
SUBTITLE = "A Real-Time Vision Workbench for Fingerspelled Hand Signs"
REPORT_TITLE = f"{TITLE}: {SUBTITLE}"

FIGURES: dict[str, str] = {
    "1.1": "fig_1_1_methodology.png",
    "1.2": "fig_1_2_conceptual_framework.png",
    "2.1": "fig_2_1_experimental_setup.png",
    "4.1": "fig_4_1_literature_timeline.png",
    "5.1": "fig_5_1_architecture.png",
    "5.2": "fig_5_2_pipeline.png",
    "5.3": "fig_5_5_mask_gallery.png",
    "5.4": "fig_5_6_segmentation_stages.png",
    "5.5": "fig_5_7_overlay.png",
    "5.6": "fig_5_3_feature_split.png",
    "5.7": "fig_5_4_geometry.png",
    "6.1": "fig_6_1_paradigm.png",
    "6.2": "fig_6_2_usecase.png",
    "6.3": "fig_6_3_activity.png",
    "6.4": "fig_6_4_sequence_live.png",
    "6.5": "fig_6_5_gantt.png",
    "6.6": "fig_6_6_class.png",
    "6.7": "fig_6_7_sequence_capture.png",
    "6.8": "fig_6_8_collaboration.png",
    "6.9": "fig_6_9_state.png",
    "6.10": "fig_6_10_activity_lab.png",
    "6.11": "fig_6_11_object.png",
    "6.12": "fig_6_12_deployment.png",
    "6.13": "fig_6_13_component.png",
    "6.14": "fig_6_14_desk.png",
    "6.15": "fig_6_15_reading.png",
    "6.16": "fig_6_16_lab.png",
    "6.17": "fig_6_17_library.png",
    "6.18": "fig_6_18_training.png",
}

GRAPHS: dict[str, str] = {
    "6.1": "fig_6_19_class_distribution.png",
    "6.2": "fig_6_20_per_sign_recall.png",
    "6.3": "fig_6_21_confusion_matrix.png",
    "6.4": "fig_6_22_train_test.png",
    "6.5": "fig_6_23_support_recall.png",
}


def fig(number: str) -> Path:
    return FIG / FIGURES[number]


def graph_path(number: str) -> Path:
    return FIG / GRAPHS[number]


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"
