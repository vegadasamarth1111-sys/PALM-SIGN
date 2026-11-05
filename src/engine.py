"""The live vision engine shared by the web desk and the desktop fallback."""

from __future__ import annotations

import copy
import os
import sys
import threading
import time
import traceback
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .classifier import TrainingError, load_model, predict, train_model
from .config import (
    ACCENT_BGR,
    CAMERA_INDEX,
    COMMIT_HOLD_SECONDS,
    DEFAULT_COLLECT_COUNT,
    FEATURE_VERSION,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREEN_BGR,
    INK_BGR,
    MAX_TEXT_LENGTH,
    MIN_CONFIDENCE,
    MODEL_PATH,
    MUTED_BGR,
    PAPER_BGR,
    ROI,
    SMOOTH_WINDOW,
    TARGET_FPS,
)
from .dataset import (
    append_features,
    clear_dataset,
    dataset_summary,
    normalise_label,
)
from .features import extract_features
from .motion import MotionTracker
from .preprocess import letterbox
from .segment import Segmentation, SkinSegmenter


class PredictionSmoother:
    def __init__(self, window: int = SMOOTH_WINDOW) -> None:
        self.values: deque[tuple[str, float | None]] = deque(maxlen=window)

    def clear(self) -> None:
        self.values.clear()

    def update(self, label: str | None, confidence: float | None) -> tuple[str | None, float | None]:
        if not label:
            return None, None
        self.values.append((label, confidence))
        counts = Counter(item[0] for item in self.values)
        best_count = max(counts.values())
        tied = {label for label, count in counts.items() if count == best_count}
        chosen: str | None = None
        for recent_label, _ in reversed(self.values):
            if recent_label in tied:
                chosen = recent_label
                break
        if chosen is None:
            return None, None
        matched = [conf for label, conf in self.values if label == chosen and conf is not None]
        mean_conf = float(sum(matched) / len(matched)) if matched else None
        return chosen, mean_conf


class VisionEngine:
    """Owns the camera, the segmentation pipeline and the public app state."""

    def __init__(self, camera_index: int = CAMERA_INDEX) -> None:
        self.camera_index = int(camera_index)
        self.lock = threading.RLock()
        self.frame_condition = threading.Condition()
        self.frame_seq = 0
        self.frame_jpeg: bytes | None = None
        self.stage_jpegs: dict[str, bytes] = {}
        self.stage_counter = 0

        self.segmenter = SkinSegmenter()
        self.model_bundle = load_model(MODEL_PATH)
        self.model_load_error: str | None = None
        if MODEL_PATH.exists() and self.model_bundle is None:
            self.model_load_error = "Saved model uses an older feature version. Retrain it."

        self.smoother = PredictionSmoother()
        self.motion = MotionTracker()

        self.running = False
        self.thread: threading.Thread | None = None
        self.cap: cv2.VideoCapture | None = None

        self.camera_ok = False
        self.camera_error = "Opening camera…"
        self.fps = 0.0
        self._last_loop_time = 0.0
        self._read_failures = 0
        self._last_camera_attempt = 0.0
        self._offline_cache: tuple[str, bytes] | None = None

        self.text = ""
        self.commits = 0
        self.commit_seq = 0
        self.last_commit: str | None = None
        self.stable_label: str | None = None
        self.stable_since = 0.0
        self.commit_progress = 0.0
        self.committed_this_episode = False
        self.missing_frames = 0

        self.dataset = dataset_summary()
        self._notice = {
            "id": 0,
            "kind": "quiet",
            "text": "Ready. Show one hand inside the right-hand scan box.",
        }

        self._collect: dict[str, Any] | None = None
        self._collect_features: list[np.ndarray] = []
        self._collect_thumbs: list[np.ndarray] = []
        self._collect_started = 0.0
        self._collect_last = 0.0

        self.last_features: np.ndarray | None = None
        self.last_info: dict[str, Any] = {}
        self.last_segmentation: Segmentation | None = None
        self.overlay_frame: np.ndarray | None = None
        self.last_motion: dict[str, Any] = {
            "direction": "STILL",
            "dx": 0.0,
            "dy": 0.0,
            "magnitude": 0.0,
        }

        self.session_started = time.time()
        self.session_code = datetime.now().strftime("%H%M")

    # ------------------------------------------------------------------ thread
    def start(self) -> None:
        with self.lock:
            if self.running and self.thread and self.thread.is_alive():
                return
            self.running = True
            self.thread = threading.Thread(target=self._run, name="vision-engine", daemon=True)
            self.thread.start()

    def stop(self) -> None:
        with self.lock:
            self.running = False
        cap = self.cap
        if cap is not None:
            try:
                cap.release()
            except cv2.error:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _run(self) -> None:
        while True:
            with self.lock:
                if not self.running:
                    break
            try:
                if self.cap is None:
                    now = time.time()
                    if now - self._last_camera_attempt > 1.6:
                        self._last_camera_attempt = now
                        self.cap = self._open_camera()
                    if self.cap is None:
                        self._publish_offline()
                        time.sleep(0.25)
                        continue

                ok, frame = self.cap.read()
                if not ok or frame is None:
                    self._read_failures += 1
                    with self.lock:
                        self.camera_ok = False
                        self.camera_error = "Camera opened but no frame arrived. Retrying…"
                    if self._read_failures >= 18:
                        self._release_camera()
                        self._read_failures = 0
                    self._publish_offline()
                    time.sleep(0.08)
                    continue

                self._read_failures = 0
                if frame.shape[1] != FRAME_WIDTH or frame.shape[0] != FRAME_HEIGHT:
                    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
                frame = cv2.flip(frame, 1)

                loop_start = time.perf_counter()
                with self.lock:
                    self.camera_ok = True
                    self.camera_error = ""
                    overlay = self._process_frame(frame)
                    jpeg = self._encode(overlay, quality=82)
                self._publish_frame(jpeg)

                now = time.time()
                if self._last_loop_time:
                    instant = 1.0 / max(now - self._last_loop_time, 1e-6)
                    self.fps = (self.fps * 0.88) + (instant * 0.12) if self.fps else instant
                self._last_loop_time = now

                elapsed = time.perf_counter() - loop_start
                delay = max(0.0, (1.0 / TARGET_FPS) - elapsed)
                if delay:
                    time.sleep(delay)
            except Exception as exc:  # Keep the camera alive even if one frame fails.
                with self.lock:
                    self.camera_error = f"Pipeline error: {exc}"
                    self.camera_ok = False
                traceback.print_exc(file=sys.stderr)
                time.sleep(0.3)

    def _open_camera(self) -> cv2.VideoCapture | None:
        backends: list[int] = []
        if sys.platform.startswith("win"):
            backends.append(cv2.CAP_DSHOW)
        backends.append(cv2.CAP_ANY)
        for backend in backends:
            cap = cv2.VideoCapture(self.camera_index, backend)
            if not cap.isOpened():
                cap.release()
                continue
            try:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except cv2.error:
                pass
            ok, _ = cap.read()
            if ok:
                with self.lock:
                    self.camera_ok = True
                    self.camera_error = ""
                return cap
            cap.release()
        with self.lock:
            self.camera_ok = False
            self.camera_error = (
                "Camera 0 is unavailable. Close other camera apps or check Windows camera access."
            )
        return None

    def _release_camera(self) -> None:
        cap = self.cap
        self.cap = None
        if cap is not None:
            try:
                cap.release()
            except cv2.error:
                pass

    # ------------------------------------------------------------- frame logic
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        now = time.monotonic()
        seg = self.segmenter.segment(frame)
        x1, y1, x2, y2 = seg.roi_box

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hand_bbox: tuple[int, int, int, int] | None = None
        if seg.hand is not None:
            bx, by, bw, bh = cv2.boundingRect(seg.hand)
            hand_bbox = (x1 + bx, y1 + by, bw, bh)

        motion = self.motion.update(gray, hand_bbox or (x1, y1, x2 - x1, y2 - y1))
        self.last_motion = motion

        valid = False
        features = np.zeros((0,), dtype=np.float32)
        info: dict[str, Any] = {}
        if seg.hand is not None:
            hand_features = extract_features(seg.hand, frame.shape, seg.hull)
            if hand_features.info.get("valid"):
                valid = True
                features = hand_features.vector
                info = hand_features.info
                info["bbox"] = (
                    x1 + info["bbox"][0],
                    y1 + info["bbox"][1],
                    info["bbox"][2],
                    info["bbox"][3],
                )
                # The defect indices are local to the ROI contour.
                info["bbox_local"] = tuple(int(v) for v in cv2.boundingRect(seg.hand))
                info["defects_global"] = [
                    (x1 + p[0], y1 + p[1]) for p in info.get("defects", [])
                ]

        self.last_features = features if valid else None
        self.last_info = info
        self.last_segmentation = seg

        raw_label: str | None = None
        raw_conf: float | None = None
        mode = "model" if self.model_bundle is not None else "shape"
        if valid and self.model_bundle is not None:
            try:
                raw_label, raw_conf = predict(self.model_bundle, features)
            except Exception:
                traceback.print_exc(file=sys.stderr)
                raw_label, raw_conf = None, None

        if valid:
            self.missing_frames = 0
            self.smoother.update(
                raw_label if mode == "model" else str(info.get("finger_estimate", "?")),
                raw_conf if mode == "model" else None,
            )
            smooth_label, smooth_conf = self.smoother.values[-1] if self.smoother.values else (None, None)
            if mode == "model":
                smooth_label, smooth_conf = self._smooth_result()
            else:
                smooth_label, smooth_conf = str(info.get("finger_estimate", "?")), None
        else:
            self.missing_frames += 1
            if self.missing_frames >= 6:
                self.smoother.clear()
            smooth_label, smooth_conf = None, None

        if mode == "model":
            self._update_commit(now, smooth_label, smooth_conf)
        else:
            self.stable_label = None
            self.commit_progress = 0.0
            self.stable_since = 0.0
            self.committed_this_episode = False

        if self._collect is not None:
            self._capture_training_sample(now, seg)

        overlay = self._draw_overlay(frame, seg, info, smooth_label, smooth_conf, mode, motion)
        self.overlay_frame = overlay
        self._store_stages(seg, overlay)
        return overlay

    def _smooth_result(self) -> tuple[str | None, float | None]:
        if not self.smoother.values:
            return None, None
        counts = Counter(label for label, _ in self.smoother.values if label)
        if not counts:
            return None, None
        best_count = max(counts.values())
        tied = {label for label, count in counts.items() if count == best_count}
        chosen = None
        for label, _ in reversed(self.smoother.values):
            if label in tied:
                chosen = label
                break
        if chosen is None:
            return None, None
        matched = [conf for label, conf in self.smoother.values if label == chosen and conf is not None]
        return chosen, (sum(matched) / len(matched) if matched else None)

    def _update_commit(self, now: float, label: str | None, confidence: float | None) -> None:
        candidate = label if label and confidence is not None and confidence >= MIN_CONFIDENCE else None
        if candidate is None:
            self.commit_progress = 0.0
            if self.missing_frames >= 8:
                self.stable_label = None
                self.stable_since = 0.0
                self.committed_this_episode = False
            return

        if candidate != self.stable_label:
            self.stable_label = candidate
            self.stable_since = now
            self.committed_this_episode = False

        held = now - self.stable_since if self.stable_since else 0.0
        self.commit_progress = min(1.0, held / COMMIT_HOLD_SECONDS)
        if held >= COMMIT_HOLD_SECONDS and not self.committed_this_episode:
            if self._append_auto(candidate):
                self.committed_this_episode = True
                self.commit_seq += 1
                self.last_commit = candidate
                self.commits += 1

    def _append_auto(self, label: str) -> bool:
        if label == "SPACE":
            if self.text and not self.text.endswith(" "):
                self.text = (self.text + " ")[-MAX_TEXT_LENGTH:]
                return True
            return False
        if len(label) != 1 or not label.isalnum():
            return False
        self.text = (self.text + label.upper())[-MAX_TEXT_LENGTH:]
        return True

    # ----------------------------------------------------------- data capture
    def start_collection(self, label: str, target: int = DEFAULT_COLLECT_COUNT) -> dict[str, Any]:
        clean = normalise_label(label)
        target = int(target)
        if target < 20:
            target = 20
        if target > 300:
            target = 300
        with self.lock:
            if self._collect is not None:
                raise ValueError("A capture is already running.")
            self._collect = {
                "label": clean,
                "target": target,
                "started_at": datetime.now().isoformat(timespec="seconds"),
            }
            self._collect_features = []
            self._collect_thumbs = []
            self._collect_started = time.monotonic()
            self._collect_last = 0.0
            self._notice_event(
                "capture",
                f"Capturing {clean}. Move the sign slightly so the model sees variation.",
            )
            return self._collection_state_locked()

    def cancel_collection(self) -> dict[str, Any]:
        with self.lock:
            if self._collect is None:
                return self._collection_state_locked()
            return self._finish_collection_locked("Capture stopped.")

    def _capture_training_sample(self, now: float, seg: Segmentation) -> None:
        if self._collect is None:
            return
        job = self._collect
        elapsed = now - self._collect_started
        if elapsed > 20.0:
            self._finish_collection_locked("Capture timed out after 20 seconds.")
            return
        if len(self._collect_features) >= int(job["target"]):
            self._finish_collection_locked("Capture complete.")
            return
        if now - self._collect_last < 0.048:
            return
        self._collect_last = now
        if self.last_features is None:
            return
        self._collect_features.append(self.last_features.copy())
        if len(self._collect_features) % 10 == 1 and seg.warped_mask is not None:
            self._collect_thumbs.append(seg.warped_mask.copy())
        if len(self._collect_features) >= int(job["target"]):
            self._finish_collection_locked("Capture complete.")

    def _finish_collection_locked(self, reason: str) -> dict[str, Any]:
        if self._collect is None:
            return self._collection_state_locked()
        label = str(self._collect["label"])
        rows = list(self._collect_features)
        thumbs = list(self._collect_thumbs)
        self._collect = None
        self._collect_features = []
        self._collect_thumbs = []
        if not rows:
            self._notice_event("error", "No frames saved. Keep your hand in the box while capturing.")
        else:
            try:
                count = append_features(label, np.vstack(rows), mask_thumbs=thumbs[:8])
                self.dataset = dataset_summary()
                self._notice_event(
                    "success",
                    f"Saved {len(rows)} frames for {label} ({count} total). {reason}",
                )
            except (OSError, ValueError) as exc:
                self._notice_event("error", f"Could not save capture: {exc}")
        return self._collection_state_locked()

    def _collection_state_locked(self) -> dict[str, Any]:
        if self._collect is None:
            return {"active": False, "label": None, "have": 0, "target": 0, "progress": 0.0}
        target = int(self._collect["target"])
        have = len(self._collect_features)
        return {
            "active": True,
            "label": self._collect["label"],
            "have": have,
            "target": target,
            "progress": min(1.0, have / max(target, 1)),
        }

    # --------------------------------------------------------------- training
    def train(self) -> dict[str, Any]:
        with self.lock:
            if self._collect is not None:
                raise TrainingError("Stop the capture before fitting the model.")
        report = train_model(MODEL_PATH)
        bundle = load_model(MODEL_PATH)
        if bundle is None:
            raise TrainingError("The model was written but could not be loaded.")
        with self.lock:
            self.model_bundle = bundle
            self.model_load_error = None
            self.smoother.clear()
            self.stable_label = None
            self.commit_progress = 0.0
            self.dataset = dataset_summary()
            self._notice_event(
                "success",
                f"Model fitted on {report['samples']} frames · held-out accuracy {report['accuracy'] * 100:.1f}%.",
            )
        return report

    def reload_model(self) -> None:
        bundle = load_model(MODEL_PATH)
        with self.lock:
            self.model_bundle = bundle
            self.model_load_error = None if bundle is not None else self.model_load_error

    def reset_lab(self) -> None:
        with self.lock:
            if self._collect is not None:
                raise ValueError("Stop the capture before resetting the lab.")
        clear_dataset()
        try:
            if MODEL_PATH.exists():
                os.remove(MODEL_PATH)
        except OSError as exc:
            raise ValueError(f"Could not remove the model file: {exc}") from exc
        with self.lock:
            self.model_bundle = None
            self.model_load_error = None
            self.smoother.clear()
            self.dataset = dataset_summary()
            self._notice_event("success", "Lab reset. Captures and the trained model were removed.")

    # ------------------------------------------------------------------ text
    def action(self, name: str, value: str | None = None) -> dict[str, Any]:
        with self.lock:
            if name == "space":
                if self.text and not self.text.endswith(" "):
                    self.text = (self.text + " ")[-MAX_TEXT_LENGTH:]
            elif name == "backspace":
                self.text = self.text[:-1]
            elif name == "clear":
                self.text = ""
            elif name == "append" and value:
                clean = str(value).upper()
                if len(clean) <= 3 and clean.isalnum():
                    self.text = (self.text + clean)[-MAX_TEXT_LENGTH:]
            else:
                raise ValueError("Unknown action")
            return {"text": self.text, "commits": self.commits}

    # --------------------------------------------------------------- settings
    def set_skin_preset(self, preset: str) -> dict[str, Any]:
        settings = self.segmenter.set_preset(preset)
        with self.lock:
            self._notice_event("quiet", f"Skin range set to {preset}.")
        return settings

    def set_skin_bounds(self, lower: list[int], upper: list[int]) -> dict[str, Any]:
        settings = self.segmenter.set_bounds(lower, upper)
        with self.lock:
            self._notice_event("quiet", "Custom skin range applied.")
        return settings

    # ---------------------------------------------------------------- state
    def _notice_event(self, kind: str, text: str) -> None:
        self._notice = {
            "id": int(self._notice.get("id", 0)) + 1,
            "kind": kind,
            "text": text,
        }

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            mode = "model" if self.model_bundle is not None else "shape"
            label: str | None = None
            detail = "No hand in the scan box"
            confidence: float | None = None

            if self.last_features is not None:
                if mode == "model":
                    if self.smoother.values:
                        label, confidence = self._smooth_result()
                    if label:
                        detail = "Hold steady to write"
                    else:
                        detail = "Reading the hand…"
                else:
                    fingers = int(self.last_info.get("finger_estimate", 0))
                    label = str(fingers)
                    detail = (
                        "0 fingers · closed hand"
                        if fingers == 0
                        else f"{fingers} finger{'s' if fingers != 1 else ''} · shape mode"
                    )

            if mode == "model" and label and confidence is not None and confidence < MIN_CONFIDENCE:
                detail = "Low confidence · hold steadier"

            model_info: dict[str, Any] = {
                "loaded": self.model_bundle is not None,
                "labels": list(self.model_bundle.get("labels", [])) if self.model_bundle else [],
                "accuracy": float(self.model_bundle["accuracy"]) if self.model_bundle else None,
                "train_accuracy": (
                    float(self.model_bundle.get("train_accuracy", 0.0)) if self.model_bundle else None
                ),
                "samples": int(self.model_bundle.get("samples", 0)) if self.model_bundle else 0,
                "trained_at": self.model_bundle.get("trained_at") if self.model_bundle else None,
                "test_samples": (
                    int(self.model_bundle.get("test_samples", 0)) if self.model_bundle else 0
                ),
                "class_counts": (
                    copy.deepcopy(self.model_bundle.get("class_counts", {}))
                    if self.model_bundle
                    else {}
                ),
                "metrics": (
                    copy.deepcopy(self.model_bundle.get("metrics", {}))
                    if self.model_bundle
                    else {}
                ),
                "confusion_matrix": (
                    copy.deepcopy(self.model_bundle.get("confusion_matrix", []))
                    if self.model_bundle
                    else []
                ),
                "error": self.model_load_error,
            }

            return {
                "camera_ok": bool(self.camera_ok),
                "camera_error": self.camera_error,
                "fps": round(float(self.fps), 1),
                "frame_seq": self.frame_seq,
                "mode": mode,
                "reading": {
                    "label": label,
                    "confidence": round(confidence, 4) if confidence is not None else None,
                    "detail": detail,
                    "stable_progress": round(float(self.commit_progress), 4),
                    "hold_seconds": COMMIT_HOLD_SECONDS,
                },
                "geometry": {
                    "fingers": int(self.last_info.get("finger_estimate", 0))
                    if self.last_features is not None
                    else None,
                    "solidity": round(float(self.last_info.get("solidity", 0.0)), 3)
                    if self.last_features is not None
                    else None,
                    "defects": int(self.last_info.get("defect_count", 0))
                    if self.last_features is not None
                    else None,
                    "area": round(float(self.last_info.get("area", 0.0)), 1)
                    if self.last_features is not None
                    else None,
                    "hand_found": self.last_features is not None,
                },
                "motion": copy.deepcopy(self.last_motion),
                "text": self.text,
                "commits": self.commits,
                "commit_seq": self.commit_seq,
                "last_commit": self.last_commit,
                "collect": self._collection_state_locked(),
                "dataset": copy.deepcopy(self.dataset),
                "model": model_info,
                "settings": self.segmenter.settings(),
                "notice": copy.deepcopy(self._notice),
                "session": {
                    "code": self.session_code,
                    "uptime": int(time.time() - self.session_started),
                },
                "feature_version": FEATURE_VERSION,
            }

    # ---------------------------------------------------------------- drawing
    def _draw_overlay(
        self,
        frame: np.ndarray,
        seg: Segmentation,
        info: dict[str, Any],
        label: str | None,
        confidence: float | None,
        mode: str,
        motion: dict[str, Any],
    ) -> np.ndarray:
        canvas = frame.copy()
        x1, y1, x2, y2 = seg.roi_box
        self._draw_brackets(canvas, (x1, y1, x2, y2), PAPER_BGR, 26, 2)

        # A subtle caption inside the scan zone.
        caption = "SCAN  /  ONE HAND"
        cv2.putText(
            canvas,
            caption,
            (x1 + 2, max(14, y1 - 8)),
            cv2.FONT_HERSHEY_DUPLEX,
            0.36,
            PAPER_BGR,
            1,
            cv2.LINE_AA,
        )

        if seg.faces:
            for fx, fy, fw, fh in seg.faces:
                cv2.rectangle(canvas, (fx, fy), (fx + fw, fy + fh), MUTED_BGR, 1)
                cv2.putText(
                    canvas,
                    "FACE MASK",
                    (fx, max(12, fy - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.32,
                    MUTED_BGR,
                    1,
                    cv2.LINE_AA,
                )

        if seg.hand is not None:
            hand_global = seg.hand + np.array([[x1, y1]], dtype=seg.hand.dtype)
            if seg.hull is not None:
                hull_global = seg.hull + np.array([[x1, y1]], dtype=seg.hull.dtype)
                cv2.polylines(canvas, [hull_global], True, (178, 190, 188), 1, cv2.LINE_AA)
            cv2.drawContours(canvas, [hand_global], -1, ACCENT_BGR, 2, cv2.LINE_AA)

            for point in info.get("defects_global", []):
                cv2.circle(canvas, (int(point[0]), int(point[1])), 4, ACCENT_BGR, 1, cv2.LINE_AA)
                cv2.circle(canvas, (int(point[0]), int(point[1])), 1, PAPER_BGR, -1, cv2.LINE_AA)

            bx, by, bw, bh = info.get("bbox", (x1, y1, 1, 1))
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (110, 115, 105), 1)

        # Live badge in the bottom-right of the image. Keeping it in the JPEG
        # means saved report frames carry the same reading as the web UI.
        badge_w = 150
        badge_h = 32
        bx = max(10, min(frame.shape[1] - badge_w - 10, x2 - badge_w))
        by = min(frame.shape[0] - badge_h - 12, y2 - badge_h - 10)
        cv2.rectangle(canvas, (bx, by), (bx + badge_w, by + badge_h), INK_BGR, -1)
        if label:
            shown = label if len(label) <= 6 else label[:6]
            suffix = ""
            if confidence is not None and mode == "model":
                suffix = f"  {confidence * 100:.0f}%"
            text = f"{shown}{suffix}"
            color = ACCENT_BGR
        else:
            text = "SEARCHING"
            color = MUTED_BGR
        cv2.putText(
            canvas,
            text,
            (bx + 12, by + 22),
            cv2.FONT_HERSHEY_DUPLEX,
            0.55,
            color,
            1,
            cv2.LINE_AA,
        )

        # Small motion caption in the upper-right of the scan zone.
        direction = motion.get("direction", "STILL")
        cv2.putText(
            canvas,
            f"MOTION  {direction}",
            (x2 - 154, y1 + 18),
            cv2.FONT_HERSHEY_DUPLEX,
            0.34,
            (176, 184, 178),
            1,
            cv2.LINE_AA,
        )

        if self.last_features is None:
            prompt = "PLACE HAND IN BOX"
            size = cv2.getTextSize(prompt, cv2.FONT_HERSHEY_DUPLEX, 0.52, 1)[0]
            px = x1 + max(8, ((x2 - x1) - size[0]) // 2)
            py = y1 + (y2 - y1) // 2
            cv2.putText(
                canvas,
                prompt,
                (px, py),
                cv2.FONT_HERSHEY_DUPLEX,
                0.52,
                (188, 195, 190),
                1,
                cv2.LINE_AA,
            )
        return canvas

    @staticmethod
    def _draw_brackets(
        image: np.ndarray,
        box: tuple[int, int, int, int],
        colour: tuple[int, int, int],
        length: int,
        thickness: int,
    ) -> None:
        x1, y1, x2, y2 = box
        for p1, p2 in (
            ((x1, y1), (x1 + length, y1)),
            ((x1, y1), (x1, y1 + length)),
            ((x2, y1), (x2 - length, y1)),
            ((x2, y1), (x2, y1 + length)),
            ((x1, y2), (x1 + length, y2)),
            ((x1, y2), (x1, y2 - length)),
            ((x2, y2), (x2 - length, y2)),
            ((x2, y2), (x2, y2 - length)),
        ):
            cv2.line(image, p1, p2, colour, thickness, cv2.LINE_AA)

    # --------------------------------------------------------------- streaming
    def _encode(self, image: np.ndarray, quality: int = 80) -> bytes:
        ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            return b""
        return buffer.tobytes()

    def _publish_frame(self, jpeg: bytes) -> None:
        with self.frame_condition:
            self.frame_jpeg = jpeg
            self.frame_seq += 1
            self.frame_condition.notify_all()

    def _publish_offline(self) -> None:
        error = self.camera_error or "Camera unavailable"
        key = f"{error}:{int(time.time())}"
        if self._offline_cache is None or self._offline_cache[0] != key:
            canvas = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), (25, 26, 25), dtype=np.uint8)
            for x in range(0, FRAME_WIDTH, 32):
                cv2.line(canvas, (x, 0), (x, FRAME_HEIGHT), (34, 35, 34), 1)
            for y in range(0, FRAME_HEIGHT, 32):
                cv2.line(canvas, (0, y), (FRAME_WIDTH, y), (34, 35, 34), 1)
            cv2.rectangle(canvas, (42, 42), (FRAME_WIDTH - 42, FRAME_HEIGHT - 42), (73, 75, 71), 1)
            cv2.putText(
                canvas,
                "CAMERA OFFLINE",
                (74, 205),
                cv2.FONT_HERSHEY_DUPLEX,
                0.9,
                (228, 238, 242),
                1,
                cv2.LINE_AA,
            )
            wrapped = error
            cv2.putText(
                canvas,
                wrapped[:70],
                (74, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.43,
                (160, 160, 152),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                "PALM/SIGN  /  WAITING FOR INPUT",
                (74, FRAME_HEIGHT - 76),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (100, 102, 97),
                1,
                cv2.LINE_AA,
            )
            jpeg = self._encode(canvas, quality=78)
            self._offline_cache = (key, jpeg)
        else:
            jpeg = self._offline_cache[1]
        self._publish_frame(jpeg)

    def wait_for_frame(self, last_seq: int, timeout: float = 4.0) -> tuple[int, bytes | None]:
        with self.frame_condition:
            self.frame_condition.wait_for(lambda: self.frame_seq != last_seq, timeout=timeout)
            return self.frame_seq, self.frame_jpeg

    def latest_jpeg(self) -> bytes | None:
        return self.frame_jpeg

    def stage_jpeg(self, name: str) -> bytes | None:
        return self.stage_jpegs.get(name)

    def _store_stages(self, seg: Segmentation, overlay: np.ndarray) -> None:
        self.stage_counter += 1
        if self.stage_counter % 4 != 0:
            return
        try:
            x1, y1, x2, y2 = seg.roi_box
            source = letterbox(overlay, 320, 240)
            light = letterbox(seg.light_roi, 320, 240)
            mask_vis = np.full((max(1, y2 - y1), max(1, x2 - x1), 3), (16, 17, 16), dtype=np.uint8)
            active = seg.mask_roi > 0
            mask_vis[active] = (214, 236, 224)
            if seg.hand is not None:
                cv2.drawContours(mask_vis, [seg.hand], -1, ACCENT_BGR, 2, cv2.LINE_AA)
            mask_stage = letterbox(mask_vis, 320, 240)
            warped = seg.warped_mask
            shape_stage = letterbox(
                cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR) if warped is not None else None,
                320,
                240,
                background=(16, 17, 16),
            )
            self.stage_jpegs = {
                "source": self._encode(source, 68),
                "light": self._encode(light, 68),
                "mask": self._encode(mask_stage, 68),
                "shape": self._encode(shape_stage, 68),
            }
        except Exception:
            traceback.print_exc(file=sys.stderr)

