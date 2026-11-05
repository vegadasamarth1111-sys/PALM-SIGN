"""Reading and writing the hand-feature dataset."""

from __future__ import annotations

import json
import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

from .config import DATASET_DIR, FEATURE_DIM, FEATURE_VERSION

_LABEL_RE = re.compile(r"^[A-Z0-9]{1,3}$")
_LOCK = threading.RLock()


def normalise_label(label: str) -> str:
    value = str(label or "").strip().upper()
    if not _LABEL_RE.fullmatch(value):
        raise ValueError("Labels must be 1-3 letters or numbers")
    return value


def label_dir(label: str, root: Path | None = None) -> Path:
    clean = normalise_label(label)
    return (root or DATASET_DIR) / clean


def _load_array(path: Path) -> np.ndarray:
    if not path.exists():
        return np.zeros((0, FEATURE_DIM), dtype=np.float32)
    array = np.load(path, allow_pickle=False)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.ndim != 2 or array.shape[1] != FEATURE_DIM:
        raise ValueError(f"{path} has shape {array.shape}, expected (n, {FEATURE_DIM})")
    return array.astype(np.float32)


def _meta_for(label: str, count: int) -> dict[str, Any]:
    return {
        "label": label,
        "feature_version": FEATURE_VERSION,
        "feature_dim": FEATURE_DIM,
        "samples": int(count),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def append_features(
    label: str,
    features: np.ndarray,
    mask_thumbs: Iterable[np.ndarray] | None = None,
    root: Path | None = None,
) -> int:
    """Append feature rows to a label and return the new class count."""
    clean = normalise_label(label)
    rows = np.asarray(features, dtype=np.float32)
    if rows.ndim == 1:
        rows = rows.reshape(1, -1)
    if rows.ndim != 2 or rows.shape[1] != FEATURE_DIM:
        raise ValueError(f"Expected features with shape (n, {FEATURE_DIM})")
    rows = np.nan_to_num(rows, nan=0.0, posinf=0.0, neginf=0.0)

    target_dir = label_dir(clean, root)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "features.npy"

    with _LOCK:
        existing = _load_array(target)
        combined = np.vstack((existing, rows)) if len(existing) else rows
        temp = target_dir / "features.tmp.npy"
        np.save(temp, combined.astype(np.float32))
        temp.replace(target)

        if mask_thumbs is not None:
            thumb_dir = target_dir / "masks"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%H%M%S")
            for index, image in enumerate(mask_thumbs, start=1):
                if image is None or image.size == 0:
                    continue
                if image.ndim == 2:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                thumb = cv2.resize(image, (180, 180), interpolation=cv2.INTER_AREA)
                cv2.imwrite(str(thumb_dir / f"{stamp}_{index:02d}.png"), thumb)

        (target_dir / "meta.json").write_text(
            json.dumps(_meta_for(clean, len(combined)), indent=2),
            encoding="utf-8",
        )
        return int(len(combined))


def dataset_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or DATASET_DIR
    base.mkdir(parents=True, exist_ok=True)
    classes: dict[str, int] = {}
    latest: float = 0.0
    if base.exists():
        for child in sorted(base.iterdir()):
            if not child.is_dir() or not _LABEL_RE.fullmatch(child.name):
                continue
            try:
                count = int(_load_array(child / "features.npy").shape[0])
            except (OSError, ValueError):
                count = 0
            classes[child.name] = count
            try:
                latest = max(latest, child.stat().st_mtime)
            except OSError:
                pass
    total = int(sum(classes.values()))
    updated = (
        datetime.fromtimestamp(latest, tz=timezone.utc).isoformat(timespec="seconds")
        if latest
        else None
    )
    return {
        "classes": classes,
        "label_count": len([c for c in classes.values() if c > 0]),
        "total": total,
        "updated_at": updated,
        "feature_dim": FEATURE_DIM,
        "feature_version": FEATURE_VERSION,
    }


def load_training_data(root: Path | None = None) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    base = root or DATASET_DIR
    all_rows: list[np.ndarray] = []
    all_labels: list[str] = []
    counts: dict[str, int] = {}
    for child in sorted(base.iterdir()) if base.exists() else []:
        if not child.is_dir() or not _LABEL_RE.fullmatch(child.name):
            continue
        rows = _load_array(child / "features.npy")
        if len(rows) == 0:
            continue
        all_rows.append(rows)
        all_labels.extend([child.name] * len(rows))
        counts[child.name] = len(rows)
    if not all_rows:
        return (
            np.zeros((0, FEATURE_DIM), dtype=np.float32),
            np.zeros((0,), dtype=object),
            {},
        )
    return np.vstack(all_rows).astype(np.float32), np.array(all_labels, dtype=object), counts


def clear_dataset(root: Path | None = None) -> None:
    base = root or DATASET_DIR
    with _LOCK:
        if not base.exists():
            return
        for child in list(base.iterdir()):
            if child.is_dir() and _LABEL_RE.fullmatch(child.name):
                shutil.rmtree(child, ignore_errors=True)
