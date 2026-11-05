"""Colour segmentation, face exclusion and contour analysis."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .config import CASCADE_PATH, DEFAULT_SKIN_PRESET, ROI, SETTINGS_PATH, SKIN_PRESETS
from .preprocess import apply_clahe, normalise_hand_mask

# Face detection is the slowest part of the classic pipeline, so it is run on
# a smaller image and cached between frames.
_FACE_SCALE = 0.5
_FACE_EVERY = 4


@dataclass
class Segmentation:
    frame: np.ndarray
    light: np.ndarray
    roi_box: tuple[int, int, int, int]
    light_roi: np.ndarray
    hsv_roi: np.ndarray
    mask: np.ndarray
    mask_roi: np.ndarray
    contours: list[np.ndarray] = field(default_factory=list)
    hand: np.ndarray | None = None
    hull: np.ndarray | None = None
    defects: list[tuple[int, int, int]] = field(default_factory=list)
    warped_mask: np.ndarray | None = None
    faces: list[tuple[int, int, int, int]] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)


class SkinSegmenter:
    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or SETTINGS_PATH
        self._lock = threading.RLock()
        self._frame_no = 0
        self._faces: list[tuple[int, int, int, int]] = []
        self.preset = DEFAULT_SKIN_PRESET
        self.lower = np.array(SKIN_PRESETS[self.preset]["lower"], dtype=np.uint8)
        self.upper = np.array(SKIN_PRESETS[self.preset]["upper"], dtype=np.uint8)
        self.detector: cv2.CascadeClassifier | None = None
        self._load_settings()
        self._load_detector()

    # ---------- settings ----------
    def _load_settings(self) -> None:
        if not self.settings_path.exists():
            return
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
            lower = payload.get("lower")
            upper = payload.get("upper")
            preset = payload.get("preset", "custom")
            if self._valid_bounds(lower, upper):
                self.lower = np.array(lower, dtype=np.uint8)
                self.upper = np.array(upper, dtype=np.uint8)
                self.preset = str(preset)
        except (OSError, ValueError, TypeError):
            # A broken settings file should never stop the app.
            pass

    def _save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "preset": self.preset,
            "lower": [int(v) for v in self.lower],
            "upper": [int(v) for v in self.upper],
        }
        temp = self.settings_path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp.replace(self.settings_path)

    @staticmethod
    def _valid_bounds(lower: Any, upper: Any) -> bool:
        if not isinstance(lower, (list, tuple)) or not isinstance(upper, (list, tuple)):
            return False
        if len(lower) != 3 or len(upper) != 3:
            return False
        try:
            low = [int(v) for v in lower]
            high = [int(v) for v in upper]
        except (TypeError, ValueError):
            return False
        return all(0 <= v <= 255 for v in low + high) and all(a < b for a, b in zip(low, high))

    def set_preset(self, name: str) -> dict[str, Any]:
        if name not in SKIN_PRESETS:
            raise ValueError("Unknown lighting preset")
        with self._lock:
            self.preset = name
            self.lower = np.array(SKIN_PRESETS[name]["lower"], dtype=np.uint8)
            self.upper = np.array(SKIN_PRESETS[name]["upper"], dtype=np.uint8)
            self._save_settings()
            return self.settings()

    def set_bounds(self, lower: list[int], upper: list[int]) -> dict[str, Any]:
        if not self._valid_bounds(lower, upper):
            raise ValueError("Invalid HSV range")
        with self._lock:
            self.lower = np.array([int(v) for v in lower], dtype=np.uint8)
            self.upper = np.array([int(v) for v in upper], dtype=np.uint8)
            self.preset = "custom"
            self._save_settings()
            return self.settings()

    def settings(self) -> dict[str, Any]:
        return {
            "preset": self.preset,
            "lower": [int(v) for v in self.lower],
            "upper": [int(v) for v in self.upper],
            "presets": {
                key: {
                    "label": value["label"],
                    "lower": list(value["lower"]),
                    "upper": list(value["upper"]),
                }
                for key, value in SKIN_PRESETS.items()
            },
        }

    # ---------- face detection ----------
    def _load_detector(self) -> None:
        path = CASCADE_PATH
        if not path.exists():
            fallback = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            if fallback.exists():
                path = fallback
        if not path.exists():
            return
        detector = cv2.CascadeClassifier(str(path))
        if not detector.empty():
            self.detector = detector

    def _detect_faces(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        self._frame_no += 1
        if self.detector is None:
            return []
        if self._frame_no % _FACE_EVERY != 0 and self._faces:
            return self._faces
        small = cv2.resize(frame, None, fx=_FACE_SCALE, fy=_FACE_SCALE, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        try:
            boxes = self.detector.detectMultiScale(
                gray,
                scaleFactor=1.15,
                minNeighbors=5,
                minSize=(34, 34),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )
        except cv2.error:
            return self._faces

        faces: list[tuple[int, int, int, int]] = []
        h, w = frame.shape[:2]
        for x, y, fw, fh in boxes:
            x = int(x / _FACE_SCALE)
            y = int(y / _FACE_SCALE)
            fw = int(fw / _FACE_SCALE)
            fh = int(fh / _FACE_SCALE)
            # Grow the rectangle a little: hair, ears and neck are skin too.
            pad_x = int(fw * 0.18)
            pad_y = int(fh * 0.22)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w, x + fw + pad_x)
            y2 = min(h, y + fh + pad_y)
            if x2 > x1 and y2 > y1:
                faces.append((x1, y1, x2 - x1, y2 - y1))
        self._faces = faces
        return faces

    # ---------- main pipeline ----------
    def segment(self, frame: np.ndarray) -> Segmentation:
        if frame is None or frame.size == 0:
            raise ValueError("segment received an empty frame")

        light = apply_clahe(frame, clip_limit=2.0, tile_grid=(8, 8))
        h, w = frame.shape[:2]
        x1 = int(round(ROI[0] * w))
        y1 = int(round(ROI[1] * h))
        x2 = int(round(ROI[2] * w))
        y2 = int(round(ROI[3] * h))
        x1, x2 = sorted((max(0, min(w - 1, x1)), max(0, min(w - 1, x2))))
        y1, y2 = sorted((max(0, min(h - 1, y1)), max(0, min(h - 1, y2))))
        x2 = max(x1 + 1, x2)
        y2 = max(y1 + 1, y2)

        light_roi = light[y1:y2, x1:x2]
        hsv_roi = cv2.cvtColor(light_roi, cv2.COLOR_BGR2HSV)

        with self._lock:
            lower = self.lower.copy()
            upper = self.upper.copy()
        mask_roi = cv2.inRange(hsv_roi, lower, upper)

        faces = self._detect_faces(frame)
        for fx, fy, fw, fh in faces:
            fx1 = max(x1, fx)
            fy1 = max(y1, fy)
            fx2 = min(x2, fx + fw)
            fy2 = min(y2, fy + fh)
            if fx2 > fx1 and fy2 > fy1:
                mask_roi[fy1 - y1 : fy2 - y1, fx1 - x1 : fx2 - x1] = 0

        mask_roi = cv2.medianBlur(mask_roi, 5)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        kernel_grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel_open)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_CLOSE, kernel_close)
        mask_roi = cv2.dilate(mask_roi, kernel_grow, iterations=1)

        contours, _ = cv2.findContours(
            mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        roi_area = float((x2 - x1) * (y2 - y1))
        min_area = max(1400.0, roi_area * 0.012)
        candidates = [c for c in contours if cv2.contourArea(c) >= min_area]

        hand: np.ndarray | None = None
        hull: np.ndarray | None = None
        warped: np.ndarray | None = None
        info: dict[str, Any] = {"roi": (x1, y1, x2, y2), "face_count": len(faces)}
        if candidates:
            hand = max(candidates, key=cv2.contourArea)
            hull = cv2.convexHull(hand)
            warped = normalise_hand_mask(mask_roi, hand, size=200)
            info.update(
                {
                    "area": float(cv2.contourArea(hand)),
                    "perimeter": float(cv2.arcLength(hand, True)),
                    "bbox": tuple(int(v) for v in cv2.boundingRect(hand)),
                }
            )

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = mask_roi
        return Segmentation(
            frame=frame,
            light=light,
            roi_box=(x1, y1, x2, y2),
            light_roi=light_roi,
            hsv_roi=hsv_roi,
            mask=mask,
            mask_roi=mask_roi,
            contours=candidates,
            hand=hand,
            hull=hull,
            warped_mask=warped,
            faces=faces,
            info=info,
        )
