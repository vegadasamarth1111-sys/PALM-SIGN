"""Build dataset-derived figures: A-Z mask gallery and mask processing walkthrough."""

from __future__ import annotations

import glob
import json
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

INK = "#15171a"
MUTED = "#726f66"
LINE = "#c8c1b3"
ACCENT = "#e6532f"
ACCENT_DEEP = "#c9401f"
GREEN = "#2f6b4f"
PAPER = "#f2efe7"
PAPER_LIGHT = "#faf7ee"

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 8,
        "text.color": INK,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 220,
    }
)

LABELS = [chr(c) for c in range(65, 91)]
DATA = json.loads((ROOT / "model_metrics.json").read_text())


def best_mask(label: str) -> tuple[np.ndarray, Path] | tuple[None, None]:
    """Pick the mask whose largest blob is the biggest and most central."""
    best = None
    for p in sorted(glob.glob(str(PROJECT / "dataset" / label / "masks" / "*.png"))):
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, bw = cv2.threshold(img, 40, 255, cv2.THRESH_BINARY)
        n, lab, stats, cents = cv2.connectedComponentsWithStats(bw, 8)
        if n < 2:
            continue
        i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        area = stats[i, cv2.CC_STAT_AREA]
        cx, cy = cents[i]
        h, w = img.shape
        off = np.hypot((cx - w / 2) / w, (cy - h / 2) / h)
        score = area * (1.0 - 0.6 * min(off, 1.0))
        if best is None or score > best[0]:
            best = (score, img, Path(p))
    if best is None:
        return None, None
    return best[1], best[2]


def mask_gallery() -> None:
    fig, axes = plt.subplots(4, 7, figsize=(6.3, 3.95))
    axes = axes.ravel()
    for ax, lab in zip(axes, LABELS):
        img, path = best_mask(lab)
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(lab, fontsize=9, fontweight="bold", pad=1.6, color=INK)
        for s in ax.spines.values():
            s.set_color(LINE)
            s.set_linewidth(0.6)
    for ax in axes[len(LABELS):]:
        ax.axis("off")
    fig.text(
        0.5,
        0.015,
        "One representative 180 × 180 normalised skin mask per sign, taken from the stored captures",
        ha="center",
        fontsize=7,
        color=MUTED,
        style="italic",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1), h_pad=0.9, w_pad=0.35)
    fig.savefig(FIG / "fig_5_5_mask_gallery.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote fig_5_5_mask_gallery.png")


def walkthrough(label: str = "B") -> None:
    img, path = best_mask(label)
    if img is None:
        raise SystemExit(f"no mask for {label}")
    raw = img

    # stage 1: raw stored mask
    # stage 2: threshold + largest component + morphology
    _, bw = cv2.threshold(raw, 40, 255, cv2.THRESH_BINARY)
    n, lab_img, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    clean = np.where(lab_img == idx, 255, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=2)
    clean = cv2.morphologyEx(clean, cv2.MORPH_OPEN, kernel, iterations=1)
    clean = cv2.GaussianBlur(clean, (5, 5), 0)
    _, clean = cv2.threshold(clean, 127, 255, cv2.THRESH_BINARY)

    # stage 3: contour, hull, defects
    cnts, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(cnt, returnPoints=False)
    try:
        defects = cv2.convexityDefects(cnt, hull)
    except cv2.error:
        defects = None

    overlay = cv2.cvtColor(clean, cv2.COLOR_GRAY2BGR)
    overlay[clean > 0] = (232, 233, 231)
    cv2.drawContours(overlay, [cnt], -1, (26, 23, 21), 1, cv2.LINE_AA)
    cv2.drawContours(overlay, [cv2.convexHull(cnt)], -1, (47, 83, 230), 1, cv2.LINE_AA)
    n_def = 0
    if defects is not None:
        for d in defects[:, 0]:
            s, e, f, depth = d
            if depth / 256.0 < 6:
                continue
            n_def += 1
            p = tuple(cnt[f][0])
            cv2.circle(overlay, p, 3, (31, 64, 201), -1, cv2.LINE_AA)
    overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

    # stage 4: centroid + radial signature
    M = cv2.moments(clean, binaryImage=True)
    cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
    radial = cv2.cvtColor(clean, cv2.COLOR_GRAY2RGB)
    radial[clean > 0] = (247, 241, 234)
    for ang in range(0, 360, 15):
        a = np.radians(ang)
        end = (int(cx + 110 * np.cos(a)), int(cy - 110 * np.sin(a)))
        cv2.line(radial, (int(cx), int(cy)), end, (47, 83, 230), 1, cv2.LINE_AA)
    cv2.circle(radial, (int(cx), int(cy)), 3, (26, 23, 21), -1, cv2.LINE_AA)

    panels = [
        (raw, "(a) Stored skin mask", "HSV inRange output, 180 × 180"),
        (clean, "(b) Largest component", "morphological close + open"),
        (overlay, "(c) Contour and hull", f"convex hull, {n_def} deep defects"),
        (radial, "(d) Radial signature", "centroid with 24 angular bins"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(6.4, 1.95))
    for ax, (im, title, sub) in zip(axes, panels):
        ax.imshow(im, cmap="gray" if im.ndim == 2 else None, vmin=0, vmax=255)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=7.4, fontweight="bold", pad=3)
        ax.set_xlabel(sub, fontsize=6.2, color=MUTED, labelpad=2)
        for s in ax.spines.values():
            s.set_color(LINE)
            s.set_linewidth(0.6)
    fig.tight_layout(w_pad=0.6)
    fig.savefig(FIG / "fig_5_6_segmentation_stages.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote fig_5_6_segmentation_stages.png for", label, path.name)


if __name__ == "__main__":
    mask_gallery()
    walkthrough("B")
