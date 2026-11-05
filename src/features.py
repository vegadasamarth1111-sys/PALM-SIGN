"""Hand-shape descriptors.

The vector is intentionally made of classic computer-vision measurements:
solidity / extent, convexity-defect geometry, Hu moments, Fourier descriptors
and a radial signature. Every value is scale-normalised so the same sign is
described at different distances from the camera.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from .config import (
    CONTOUR_POINTS,
    FEATURE_DIM,
    FEATURE_VERSION,
    FOURIER_BINS,
    RADIAL_BINS,
)


@dataclass
class HandFeatures:
    vector: np.ndarray
    info: dict[str, Any] = field(default_factory=dict)


def resample_contour(contour: np.ndarray, count: int = CONTOUR_POINTS) -> np.ndarray | None:
    """Sample a contour at equal arc-length intervals."""
    if contour is None or len(contour) < 3:
        return None
    points = contour.reshape(-1, 2).astype(np.float64)
    if len(points) < 2:
        return None
    # Close the curve explicitly.
    points = np.vstack((points, points[0]))
    steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(steps)))
    total = float(cumulative[-1])
    if total < 1e-6:
        return None
    targets = np.linspace(0.0, total, count, endpoint=False)
    xs = np.interp(targets, cumulative, points[:, 0])
    ys = np.interp(targets, cumulative, points[:, 1])
    return np.column_stack((xs, ys)).astype(np.float32)


def _safe_float(value: float, fallback: float = 0.0) -> float:
    value = float(value)
    if not np.isfinite(value):
        return fallback
    return value


def _defect_metrics(contour: np.ndarray, hull: np.ndarray) -> tuple[int, float, float, float, list[tuple[int, int, int]]]:
    """Return filtered defect count, normalised depths, min angle, drawable defects."""
    perimeter = cv2.arcLength(contour, True)
    if perimeter < 1e-6 or len(contour) < 5:
        return 0, 0.0, 0.0, 180.0, []

    try:
        hull_indices = cv2.convexHull(contour, returnPoints=False)
        if hull_indices is None or len(hull_indices) < 4:
            return 0, 0.0, 0.0, 180.0, []
        raw_defects = cv2.convexityDefects(contour, hull_indices)
    except cv2.error:
        return 0, 0.0, 0.0, 180.0, []

    if raw_defects is None:
        return 0, 0.0, 0.0, 180.0, []

    valid: list[dict[str, Any]] = []
    min_depth = max(7.0, perimeter * 0.018)
    for row in raw_defects:
        start_idx, end_idx, far_idx, depth_raw = [int(v) for v in row[0]]
        depth = depth_raw / 256.0
        if depth < min_depth:
            continue
        start = contour[start_idx][0].astype(np.float64)
        end = contour[end_idx][0].astype(np.float64)
        far = contour[far_idx][0].astype(np.float64)
        vec_a = start - far
        vec_b = end - far
        denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        if denom < 1e-6:
            continue
        cosine = float(np.clip(np.dot(vec_a, vec_b) / denom, -1.0, 1.0))
        angle = float(np.degrees(np.arccos(cosine)))
        if angle > 105.0:
            continue
        valid.append(
            {
                "start": start_idx,
                "end": end_idx,
                "far": far_idx,
                "depth": depth,
                "angle": angle,
            }
        )

    if not valid:
        return 0, 0.0, 0.0, 180.0, []

    # A noisy contour can yield many tiny defects. Keep the deepest ones that
    # look like real valleys between fingers.
    valid.sort(key=lambda item: item["depth"], reverse=True)
    kept = valid[:7]
    depths = np.array([item["depth"] for item in kept], dtype=np.float32) / max(perimeter, 1.0)
    angles = np.array([item["angle"] for item in kept], dtype=np.float32)
    drawable = [
        (item["start"], item["end"], item["far"])
        for item in kept
        if item["depth"] >= min_depth * 1.15
    ]
    return len(kept), float(depths.max()), float(depths.mean()), float(angles.min()), drawable


def extract_features(
    contour: np.ndarray,
    frame_shape: tuple[int, ...],
    hull_points: np.ndarray | None = None,
) -> HandFeatures:
    """Build the fixed-length feature vector for one hand contour."""
    if contour is None or len(contour) < 5:
        return HandFeatures(np.zeros(FEATURE_DIM, dtype=np.float32), {"valid": False})

    area = float(cv2.contourArea(contour))
    if area < 20:
        return HandFeatures(np.zeros(FEATURE_DIM, dtype=np.float32), {"valid": False})

    if hull_points is None:
        hull_points = cv2.convexHull(contour)
    hull_area = float(cv2.contourArea(hull_points))
    hull_perimeter = float(cv2.arcLength(hull_points, True))
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter < 1e-6 or hull_area < 1e-6:
        return HandFeatures(np.zeros(FEATURE_DIM, dtype=np.float32), {"valid": False})

    x, y, bw, bh = cv2.boundingRect(contour)
    bbox_area = max(float(bw * bh), 1.0)
    rect = cv2.minAreaRect(contour)
    rect_w, rect_h = rect[1]
    long_side = max(float(rect_w), float(rect_h), 1.0)
    short_side = max(min(float(rect_w), float(rect_h)), 1.0)

    solidity = _safe_float(area / hull_area)
    extent = _safe_float(area / bbox_area)
    elongation = _safe_float(long_side / short_side - 1.0)
    circularity = _safe_float(4.0 * np.pi * area / (perimeter * perimeter))

    defect_count, max_depth, mean_depth, min_angle, drawable_defects = _defect_metrics(
        contour, hull_points
    )

    hull_vertices = cv2.approxPolyDP(hull_points, max(2.0, hull_perimeter * 0.025), True)
    hull_vertex_count = len(hull_vertices)

    # A closed hand has almost no useful valleys. Solidity and hull corners are
    # better hints than a raw defect count for the 0 / 1 finger edge case.
    if defect_count == 0:
        finger_estimate = 0 if solidity > 0.87 or hull_vertex_count <= 4 else 1
    else:
        finger_estimate = min(5, defect_count + 1)

    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).reshape(-1)
    hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-30)
    hu = np.clip(hu, -20.0, 20.0).astype(np.float32)

    sampled = resample_contour(contour, CONTOUR_POINTS)
    if sampled is None:
        return HandFeatures(np.zeros(FEATURE_DIM, dtype=np.float32), {"valid": False})

    centroid = sampled.mean(axis=0)
    centred = sampled - centroid
    complex_points = centred[:, 0].astype(np.float64) + 1j * centred[:, 1].astype(np.float64)
    spectrum = np.abs(np.fft.fft(complex_points))
    normaliser = float(spectrum[1]) if len(spectrum) > 1 else 0.0
    if normaliser < 1e-8:
        normaliser = float(np.max(spectrum)) if np.max(spectrum) > 0 else 1.0
    fourier = spectrum[1 : FOURIER_BINS + 1] / normaliser
    if len(fourier) < FOURIER_BINS:
        fourier = np.pad(fourier, (0, FOURIER_BINS - len(fourier)))
    fourier = np.clip(fourier, 0.0, 20.0).astype(np.float32)

    radii = np.linalg.norm(centred, axis=1)
    max_radius = float(radii.max()) if len(radii) else 0.0
    if max_radius < 1e-6:
        radial = np.zeros(RADIAL_BINS, dtype=np.float32)
    else:
        radial = radii / max_radius
        angles = (np.arctan2(centred[:, 1], centred[:, 0]) + np.pi) / (2.0 * np.pi)
        bin_ids = np.clip((angles * RADIAL_BINS).astype(int), 0, RADIAL_BINS - 1)
        sums = np.zeros(RADIAL_BINS, dtype=np.float64)
        counts = np.zeros(RADIAL_BINS, dtype=np.float64)
        for bin_id, value in zip(bin_ids, radial):
            sums[bin_id] += value
            counts[bin_id] += 1.0
        non_empty = counts > 0
        radial = np.zeros(RADIAL_BINS, dtype=np.float32)
        radial[non_empty] = (sums[non_empty] / counts[non_empty]).astype(np.float32)
        if np.any(non_empty):
            radial[~non_empty] = float(radial[non_empty].mean())
        radial = np.clip(radial, 0.0, 1.5)

    vector = np.concatenate(
        (
            np.array(
                [
                    solidity,
                    extent,
                    elongation,
                    circularity,
                    finger_estimate / 5.0,
                    defect_count / 5.0,
                    max_depth,
                    mean_depth,
                    min_angle / 180.0,
                    hull_vertex_count / 10.0,
                ],
                dtype=np.float32,
            ),
            hu,
            fourier,
            radial,
        )
    ).astype(np.float32)

    vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)
    if vector.shape[0] != FEATURE_DIM:
        raise RuntimeError(
            f"Feature contract mismatch: got {vector.shape[0]}, expected {FEATURE_DIM}"
        )

    info = {
        "valid": True,
        "area": area,
        "solidity": solidity,
        "extent": extent,
        "elongation": elongation,
        "circularity": circularity,
        "finger_estimate": int(finger_estimate),
        "defect_count": int(defect_count),
        "hull_vertices": int(hull_vertex_count),
        "bbox": (int(x), int(y), int(bw), int(bh)),
        "defects": drawable_defects,
        "feature_version": FEATURE_VERSION,
    }
    return HandFeatures(vector, info)


def feature_names() -> list[str]:
    names = [
        "solidity",
        "extent",
        "elongation",
        "circularity",
        "finger_estimate",
        "defect_count",
        "max_defect_depth",
        "mean_defect_depth",
        "min_defect_angle",
        "hull_vertex_count",
    ]
    names += [f"hu_{i}" for i in range(1, 8)]
    names += [f"fourier_{i}" for i in range(1, FOURIER_BINS + 1)]
    names += [f"radial_{i}" for i in range(1, RADIAL_BINS + 1)]
    if len(names) != FEATURE_DIM:
        raise RuntimeError("Feature names do not match FEATURE_DIM")
    return names
