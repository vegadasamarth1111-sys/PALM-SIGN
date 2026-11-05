"""Small, reusable image helpers used by the live pipeline and training."""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np


@lru_cache(maxsize=8)
def _clahe(clip_limit: float, tile_w: int, tile_h: int) -> cv2.CLAHE:
    return cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=(tile_w, tile_h))


def apply_clahe(
    bgr: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Equalise luminance in LAB space without shifting the colour balance."""
    if bgr is None or bgr.size == 0:
        raise ValueError("apply_clahe received an empty image")
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    l_chan = _clahe(float(clip_limit), int(tile_grid[0]), int(tile_grid[1])).apply(l_chan)
    return cv2.cvtColor(cv2.merge((l_chan, a_chan, b_chan)), cv2.COLOR_LAB2BGR)


def apply_equalise_hist(bgr: np.ndarray) -> np.ndarray:
    """Plain histogram equalisation. Kept for the report comparison."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    l_chan = cv2.equalizeHist(l_chan)
    return cv2.cvtColor(cv2.merge((l_chan, a_chan, b_chan)), cv2.COLOR_LAB2BGR)


def order_points(points: np.ndarray) -> np.ndarray:
    """Order four points as top-left, top-right, bottom-right, bottom-left."""
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    ordered = np.zeros((4, 2), dtype=np.float32)
    point_sum = pts.sum(axis=1)
    point_diff = np.diff(pts, axis=1).reshape(-1)
    ordered[0] = pts[np.argmin(point_sum)]
    ordered[2] = pts[np.argmax(point_sum)]
    ordered[1] = pts[np.argmin(point_diff)]
    ordered[3] = pts[np.argmax(point_diff)]
    return ordered


def normalise_hand_mask(
    mask: np.ndarray,
    contour: np.ndarray | None,
    size: int = 200,
) -> np.ndarray:
    """Rotate/scale the hand mask into a consistent square for inspection."""
    canvas = np.zeros((size, size), dtype=np.uint8)
    if contour is None or len(contour) < 5:
        return canvas
    rect = cv2.minAreaRect(contour)
    if rect[1][0] < 2 or rect[1][1] < 2:
        return canvas
    box = cv2.boxPoints(rect)
    src = order_points(box)
    dst = np.array(
        [[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(mask, matrix, (size, size), flags=cv2.INTER_NEAREST)
    # Keep the hand away from the border so it is easier to read visually.
    inner = cv2.resize(warped, (size - 20, size - 20), interpolation=cv2.INTER_NEAREST)
    canvas[10 : size - 10, 10 : size - 10] = inner
    return canvas


def letterbox(
    image: np.ndarray,
    width: int,
    height: int,
    background: int | tuple[int, int, int] = 20,
) -> np.ndarray:
    """Resize an image into a fixed canvas without changing its aspect ratio."""
    if image is None or image.size == 0:
        return np.full((height, width, 3), background, dtype=np.uint8)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    src_h, src_w = image.shape[:2]
    scale = min(width / src_w, height / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.full((height, width, 3), background, dtype=np.uint8)
    x = (width - new_w) // 2
    y = (height - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def safe_roi(frame: np.ndarray, roi: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    """Convert a normalised ROI into clamped pixel coordinates."""
    h, w = frame.shape[:2]
    x1 = int(round(roi[0] * w))
    y1 = int(round(roi[1] * h))
    x2 = int(round(roi[2] * w))
    y2 = int(round(roi[3] * h))
    x1, x2 = sorted((max(0, min(w - 1, x1)), max(0, min(w - 1, x2))))
    y1, y2 = sorted((max(0, min(h - 1, y1)), max(0, min(h - 1, y2))))
    return x1, y1, max(x1 + 1, x2), max(y1 + 1, y2)
