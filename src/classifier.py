"""Train, save and run the hand-shape classifier."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .config import (
    FEATURE_DIM,
    FEATURE_VERSION,
    MIN_CLASSES,
    MIN_SAMPLES_PER_CLASS,
    MIN_TOTAL_SAMPLES,
    MODEL_PATH,
)
from .dataset import load_training_data


class TrainingError(RuntimeError):
    pass


def _json_metrics(
    labels: list[str],
    truth: np.ndarray,
    predicted: np.ndarray,
) -> tuple[list[list[int]], dict[str, Any]]:
    matrix = confusion_matrix(truth, predicted, labels=labels)
    report = classification_report(
        truth,
        predicted,
        labels=labels,
        zero_division=0,
        output_dict=True,
    )
    serialisable = {
        "macro_f1": float(report.get("macro avg", {}).get("f1-score", 0.0)),
        "weighted_f1": float(report.get("weighted avg", {}).get("f1-score", 0.0)),
        "per_class": {
            label: {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }
            for label in labels
            if label in report
        },
    }
    return matrix.tolist(), serialisable


def train_model(model_path: Path | None = None) -> dict[str, Any]:
    target = model_path or MODEL_PATH
    features, labels, counts = load_training_data()
    if len(features) == 0:
        raise TrainingError("No samples yet. Collect at least two signs first.")

    classes = sorted(counts.keys())
    if len(classes) < MIN_CLASSES:
        raise TrainingError(f"Collect at least {MIN_CLASSES} different signs.")
    small = {label: count for label, count in counts.items() if count < MIN_SAMPLES_PER_CLASS}
    if small:
        detail = ", ".join(f"{label}={count}" for label, count in sorted(small.items()))
        raise TrainingError(
            f"Each sign needs at least {MIN_SAMPLES_PER_CLASS} frames. Add more for: {detail}"
        )
    if len(features) < MIN_TOTAL_SAMPLES:
        raise TrainingError(f"Collect at least {MIN_TOTAL_SAMPLES} frames in total.")
    if features.shape[1] != FEATURE_DIM:
        raise TrainingError("Dataset feature size does not match this version of the app.")

    # A tiny per-class count can make stratification impossible. Ten samples
    # per class is already the minimum, so 25% leaves at least two for testing.
    test_count = max(len(classes) * 2, int(round(len(features) * 0.25)))
    test_count = min(test_count, len(features) - len(classes))
    test_size = test_count / len(features)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=test_size,
        random_state=42,
        stratify=labels,
    )

    evaluation_model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "svc",
                SVC(
                    kernel="rbf",
                    C=8.0,
                    gamma="scale",
                    probability=True,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    evaluation_model.fit(x_train, y_train)
    predicted = evaluation_model.predict(x_test)
    accuracy = float(accuracy_score(y_test, predicted))
    matrix, report = _json_metrics(classes, np.asarray(y_test), np.asarray(predicted))
    train_accuracy = float(accuracy_score(y_train, evaluation_model.predict(x_train)))

    # Refit on everything before deployment. The reported score remains the
    # honest held-out number.
    deployment_model = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "svc",
                SVC(
                    kernel="rbf",
                    C=8.0,
                    gamma="scale",
                    probability=True,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    deployment_model.fit(features, labels)

    trained_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bundle: dict[str, Any] = {
        "model": deployment_model,
        "labels": classes,
        "feature_version": FEATURE_VERSION,
        "feature_dim": FEATURE_DIM,
        "samples": int(len(features)),
        "class_counts": {label: int(count) for label, count in counts.items()},
        "accuracy": accuracy,
        "train_accuracy": train_accuracy,
        "test_samples": int(len(y_test)),
        "trained_at": trained_at,
        "confusion_matrix": matrix,
        "metrics": report,
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp.joblib")
    joblib.dump(bundle, temp)
    os.replace(temp, target)

    return {
        "labels": classes,
        "samples": int(len(features)),
        "class_counts": {label: int(count) for label, count in counts.items()},
        "accuracy": accuracy,
        "train_accuracy": train_accuracy,
        "test_samples": int(len(y_test)),
        "trained_at": trained_at,
        "confusion_matrix": matrix,
        "metrics": report,
    }


def load_model(model_path: Path | None = None) -> dict[str, Any] | None:
    target = model_path or MODEL_PATH
    if not target.exists():
        return None
    try:
        bundle = joblib.load(target)
    except Exception:
        return None
    if not isinstance(bundle, dict) or "model" not in bundle:
        return None
    if bundle.get("feature_version") != FEATURE_VERSION:
        return None
    if int(bundle.get("feature_dim", 0)) != FEATURE_DIM:
        return None
    return bundle


def predict(bundle: dict[str, Any] | None, features: np.ndarray) -> tuple[str | None, float | None]:
    if bundle is None:
        return None, None
    row = np.asarray(features, dtype=np.float32).reshape(1, -1)
    model: Pipeline = bundle["model"]
    label = str(model.predict(row)[0])
    confidence: float | None = None
    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(row)[0]
            confidence = float(np.max(probabilities))
        except (AttributeError, ValueError):
            confidence = None
    return label, confidence
