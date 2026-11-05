"""Dense optical-flow motion readout for dynamic signs."""

from __future__ import annotations

from collections import deque
from typing import Any

import cv2
import numpy as np


class MotionTracker:
    """Track the dominant local motion between frames.

    This is deliberately a readout rather than a gesture classifier. The live
    label comes from the static shape model; motion is shown separately so the
    report can demonstrate Farneback flow and its limits.
    """

    def __init__(self, history: int = 15) -> None:
        self.history: deque[tuple[float, float, float]] = deque(maxlen=history)
        self.previous: np.ndarray | None = None
        self.small_size = (160, 120)

    def reset(self) -> None:
        self.previous = None
        self.history.clear()

    def update(self, gray: np.ndarray, bbox: tuple[int, int, int, int] | None = None) -> dict[str, Any]:
        if gray is None or gray.size == 0:
            return {"direction": "STILL", "dx": 0.0, "dy": 0.0, "magnitude": 0.0}

        if bbox is not None:
            x, y, w, h = bbox
            pad = 18
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(gray.shape[1], x + w + pad)
            y2 = min(gray.shape[0], y + h + pad)
            crop = gray[y1:y2, x1:x2]
        else:
            crop = gray

        if crop.size == 0:
            return {"direction": "STILL", "dx": 0.0, "dy": 0.0, "magnitude": 0.0}

        small = cv2.resize(crop, self.small_size, interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (5, 5), 0)

        if self.previous is None or self.previous.shape != small.shape:
            self.previous = small
            return {"direction": "STILL", "dx": 0.0, "dy": 0.0, "magnitude": 0.0}

        flow = cv2.calcOpticalFlowFarneback(
            self.previous,
            small,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        self.previous = small
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        active = magnitude > 0.6
        if not np.any(active):
            dx = dy = 0.0
            mag = 0.0
        else:
            dx = float(np.median(flow[..., 0][active]))
            dy = float(np.median(flow[..., 1][active]))
            mag = float(np.median(magnitude[active]))

        self.history.append((dx, dy, mag))
        recent = np.array(self.history, dtype=np.float32)
        if len(recent) >= 5:
            dx = float(np.median(recent[-5:, 0]))
            dy = float(np.median(recent[-5:, 1]))
            mag = float(np.median(recent[-5:, 2]))

        direction = "STILL"
        if mag >= 0.65:
            if abs(dx) > abs(dy) * 1.35:
                direction = "RIGHT" if dx > 0 else "LEFT"
            elif abs(dy) > abs(dx) * 1.35:
                direction = "DOWN" if dy > 0 else "UP"
            else:
                direction = "DIAGONAL"

        # A simple reversal count gives the UI a "wave" hint without adding a
        # second classifier.
        if len(recent) >= 12:
            signs = np.sign(recent[-12:, 0])
            nonzero = signs[np.abs(recent[-12:, 0]) > 0.35]
            if len(nonzero) >= 6:
                flips = np.count_nonzero(np.diff(nonzero) != 0)
                if flips >= 3 and mag > 0.8:
                    direction = "WAVE"

        return {
            "direction": direction,
            "dx": round(dx, 2),
            "dy": round(dy, 2),
            "magnitude": round(mag, 2),
        }
