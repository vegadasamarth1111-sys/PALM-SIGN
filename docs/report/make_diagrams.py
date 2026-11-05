"""Generate the schematic and UML diagrams for the PALM/SIGN report."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (
    Circle,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
    Wedge,
)

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

INK = "#15171a"
MUTED = "#726f66"
LINE = "#b9b2a4"
ACCENT = "#e6532f"
ACCENT_DEEP = "#c9401f"
GREEN = "#2f6b4f"
PAPER = "#f2efe7"
PAPER_LIGHT = "#faf7ee"
PAPER_DEEP = "#e7e1d4"
CREAM = "#f3ead9"

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


def canvas(w: float, h: float, xmax: float = 100, ymax: float = 100, equal: bool = True):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_aspect("equal" if equal else "auto")
    ax.axis("off")
    return fig, ax


def box(
    ax,
    x,
    y,
    w,
    h,
    text,
    fc="white",
    ec=INK,
    fs=8,
    bold=False,
    lw=1.1,
    rounded=0.0,
    color=INK,
    align="center",
    pad=0.0,
    ls="-",
    z=2,
):
    if rounded:
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad={pad},rounding_size={rounded}",
            facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls, zorder=z,
        )
    else:
        patch = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                          linewidth=lw, linestyle=ls, zorder=z)
    ax.add_patch(patch)
    if text:
        ax.text(
            x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", zorder=z + 1,
            linespacing=1.25,
        )
    return patch


def arrow(ax, p1, p2, color=INK, lw=1.0, style="-|>", ls="-", rad=0.0, z=3, shrink=2, ms=9):
    a = FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=ms, color=color,
        linewidth=lw, linestyle=ls, zorder=z,
        connectionstyle=f"arc3,rad={rad}", shrinkA=shrink, shrinkB=shrink,
    )
    ax.add_patch(a)
    return a


def label(ax, x, y, text, fs=7, color=MUTED, ha="center", va="center",
          bold=False, style="normal", rot=0, bg=None, z=5):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.18", fc=bg, ec="none")
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", fontstyle=style,
            rotation=rot, zorder=z, linespacing=1.2, **kw)


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- 1.1 method
def methodology():
    fig, ax = canvas(6.2, 6.4, 110, 100)
    cx = 38
    W, H = 50, 5.6
    steps = [
        (92, "Problem definition and scope"),
        (84, "Literature and tool study"),
        (76, "Camera setup and A\u2013Z data capture"),
        (68, "Pre-processing and hand segmentation"),
        (60, "61-D feature extraction"),
        (52, "SVC training and held-out evaluation"),
    ]
    for y, text in steps:
        box(ax, cx - W / 2, y - H / 2, W, H, text, fc=PAPER_LIGHT, fs=7.6, rounded=0.6)
    for (y1, _), (y2, _) in zip(steps, steps[1:]):
        arrow(ax, (cx, y1 - H / 2), (cx, y2 + H / 2))

    # decision diamond
    dy = 40
    diamond = Polygon(
        [(cx, dy + 6.4), (cx + 17, dy), (cx, dy - 6.4), (cx - 17, dy)],
        closed=True, facecolor="#fdf1ec", edgecolor=ACCENT_DEEP, lw=1.1, zorder=2,
    )
    ax.add_patch(diamond)
    label(ax, cx, dy, "Held-out\naccuracy\n\u2265 95%?", fs=7.2, color=INK)
    arrow(ax, (cx, steps[-1][0] - H / 2), (cx, dy + 6.4))

    # yes -> workbench
    box(ax, cx - W / 2, 24, W, H, "Flask web workbench and UI", fc=PAPER_LIGHT, fs=7.4, rounded=0.6)
    arrow(ax, (cx, dy - 6.4), (cx, 24 + H / 2))
    label(ax, cx + 3.0, 30.4, "yes", fs=6.4, color=GREEN, bold=True, ha="left", bg="white")

    box(ax, cx - W / 2, 12, W, H, "Testing, tuning and report", fc=CREAM, fs=7.4, rounded=0.6)
    arrow(ax, (cx, 24), (cx, 12 + H / 2))

    # no -> back to feature extraction
    ax.plot([cx + 17, 84, 84], [dy, dy, 60], color=ACCENT_DEEP, lw=1.0, ls=(0, (4, 2)), zorder=1)
    arrow(ax, (84, 60), (cx + W / 2, 60), color=ACCENT_DEEP, ls=(0, (4, 2)))
    label(ax, 86.5, 50, "no \u2014 tune features", fs=6.2, color=ACCENT_DEEP, rot=90, bg="white")

    # iterative note
    ax.plot([cx - W / 2, 10, 10], [68, 68, 60], color=LINE, lw=0.8, ls=(0, (2, 2)))
    arrow(ax, (10, 60), (cx - W / 2, 60), color=LINE, lw=0.8, ls=(0, (2, 2)))
    label(ax, 11.5, 54.6, "repeat until\nstable", fs=5.6, color=MUTED, bg="white")
    save(fig, "fig_1_1_methodology.png")


# ------------------------------------------------------- 1.2 conceptual frame
def conceptual():
    fig, ax = canvas(6.4, 3.0)
    blocks = [
        (4, "Acquisition", "Webcam frame\n640 × 480 BGR", PAPER_LIGHT),
        (27, "Representation", "61-D scale-free\nshape descriptor", PAPER_LIGHT),
        (50, "Recognition", "StandardScaler\n+ RBF SVC", "#eef4f0"),
        (73, "Presentation", "Letter, confidence\nand transcript", "#fdf1ec"),
    ]
    for x, title, body, fc in blocks:
        box(ax, x, 42, 20, 34, "", fc=fc, ec=INK, rounded=0.8)
        label(ax, x + 10, 67, title, fs=8, color=INK, bold=True)
        label(ax, x + 10, 53, body, fs=6.8, color=MUTED)
    for x in (24, 47, 70):
        arrow(ax, (x, 59), (x + 3, 59), lw=1.2)

    # dataset feedback
    box(ax, 27, 8, 43, 18, "Dataset store — 26 signs, 6,983 frames\n(numpy arrays + JSON summary)",
        fc=CREAM, fs=6.8, rounded=0.6)
    arrow(ax, (37, 26), (37, 42), color=GREEN, ls=(0, (4, 2)))
    label(ax, 34, 33, "train", fs=6.2, color=GREEN, rot=90, ha="right")
    arrow(ax, (83, 42), (70, 26), color=GREEN, ls=(0, (4, 2)), rad=-0.25)
    label(ax, 80, 33, "capture", fs=6.2, color=GREEN)
    save(fig, "fig_1_2_conceptual_framework.png")


# --------------------------------------------------------- 2.1 setup schematic
def setup():
    fig, ax = canvas(6.4, 3.4)
    # desk line
    ax.plot([2, 98], [26, 26], color=INK, lw=1.4)
    # laptop base + screen
    ax.add_patch(Polygon([(46, 26), (76, 26), (78, 30), (44, 30)],
                         closed=True, facecolor=PAPER_DEEP, edgecolor=INK, lw=1.1))
    box(ax, 49, 30, 24, 17, "", fc="#2b2d30", ec=INK, rounded=0.3)
    label(ax, 61, 39, "PALM / SIGN\nworkbench", fs=6.2, color=CREAM)
    label(ax, 61, 33.5, "127.0.0.1:5000", fs=5.4, color="#9d9a91")

    # webcam on tripod
    box(ax, 14, 52, 12, 7, "", fc=INK, ec=INK, rounded=0.5)
    ax.add_patch(Circle((20, 55.5), 1.7, facecolor="#4b5563", edgecolor=CREAM, lw=0.8))
    ax.plot([20, 20], [52, 40], color=INK, lw=1.2)
    ax.plot([16, 24], [40, 40], color=INK, lw=1.2)
    ax.plot([20, 20], [40, 26], color=INK, lw=1.2)
    label(ax, 20, 64, "USB webcam\n640×480 @ 30 fps", fs=6.2)

    # hand
    hand_x, hand_y = 36, 42
    ax.add_patch(Rectangle((30, 33), 13, 20, facecolor="none", edgecolor=ACCENT,
                           lw=0.9, ls=(0, (3, 2))))
    palm = FancyBboxPatch((33.5, 36), 6, 9, boxstyle="round,pad=0.4,rounding_size=1.6",
                          facecolor=CREAM, edgecolor=INK, lw=1.0)
    ax.add_patch(palm)
    for dx, top in [(-2.4, 50), (-0.8, 52), (0.9, 51.5), (2.5, 49)]:
        ax.add_patch(FancyBboxPatch((36.5 + dx, 44), 1.2, top - 44,
                                    boxstyle="round,pad=0.15,rounding_size=0.6",
                                    facecolor=CREAM, edgecolor=INK, lw=0.8))
    ax.add_patch(FancyBboxPatch((32.2, 40), 1.4, 5,
                                boxstyle="round,pad=0.12,rounding_size=0.6",
                                facecolor=CREAM, edgecolor=INK, lw=0.8))
    label(ax, 36.5, 29, "hand inside ROI", fs=5.6, color=ACCENT_DEEP)

    # distance dimension line
    ax.plot([28, 28], [44, 57], color=MUTED, lw=0.7)
    ax.plot([27, 29], [44, 44], color=MUTED, lw=0.7)
    ax.plot([27, 29], [57, 57], color=MUTED, lw=0.7)
    label(ax, 26.5, 50.5, "40–70 cm", fs=5.8, color=MUTED, rot=90, ha="center")

    # lamp
    ax.plot([86, 86], [26, 62], color=INK, lw=1.1)
    ax.add_patch(Polygon([(82, 62), (90, 62), (88, 66), (84, 66)],
                         closed=True, facecolor=CREAM, edgecolor=INK, lw=1.0))
    for a in (-40, -20, 0, 20, 40):
        ax.plot([86, 86 + 5 * np.sin(np.radians(a))], [62, 62 - 5 * np.cos(np.radians(a))],
                color="#d9a441", lw=0.6)
    label(ax, 86, 69, "diffused\nfront light", fs=5.8, color=MUTED)

    # background note
    label(ax, 96, 20, "plain, non-skin\nbackground", fs=5.8, color=MUTED, ha="right")
    save(fig, "fig_2_1_experimental_setup.png")


# ----------------------------------------------------------- 5.1 architecture
def architecture():
    fig, ax = canvas(6.3, 4.0, equal=False)
    layers = [
        (86, 12, "Presentation layer", "Browser — HTML/CSS/JS desk, video stream, sign library, training panel"),
        (70, 12, "Application layer", "Flask routes /api/state /api/collect /api/train /api/reset, /video_feed"),
        (54, 12, "Domain layer", "VisionEngine thread · Segmentation · Features · Motion · Classifier"),
        (38, 12, "Data layer", "dataset/<SIGN>/*.npy · models/sign_model.joblib · settings.json"),
        (22, 12, "Hardware layer", "USB webcam (OpenCV VideoCapture) · display"),
    ]
    for y, h, title, body in layers:
        box(ax, 6, y, 88, h, "", fc=PAPER_LIGHT, ec=INK, rounded=0.6)
        label(ax, 10, y + h / 2, title, fs=7.4, color=INK, bold=True, ha="left")
        label(ax, 38, y + h / 2, body, fs=6.1, color=MUTED, ha="left")

    for y1, y2 in [(86, 82), (70, 66), (54, 50), (38, 34)]:
        arrow(ax, (50, y1), (50, y2), style="<|-|>", lw=0.9, ms=5, shrink=0)

    # side annotations
    label(ax, 97, 92, "user", fs=6, color=MUTED, rot=90)
    label(ax, 97, 76, "HTTP", fs=6, color=MUTED, rot=90)
    label(ax, 97, 60, "in-process", fs=6, color=MUTED, rot=90)
    label(ax, 97, 44, "files", fs=6, color=MUTED, rot=90)
    label(ax, 97, 28, "USB", fs=6, color=MUTED, rot=90)
    save(fig, "fig_5_1_architecture.png")


# --------------------------------------------------------------- 5.2 pipeline
def pipeline():
    fig, ax = canvas(6.5, 4.4, equal=False)
    top = [
        (2, "1  Frame", "640×480 BGR\nmirror flip"),
        (21, "2  Illumination", "CLAHE on L\n(LAB space)"),
        (40, "3  Skin mask", "HSV inRange\n+ morphology"),
        (59, "4  Face removal", "Haar cascade\nexcluded"),
        (78, "5  Largest hand", "ROI + contour\narea filter"),
    ]
    for x, title, body in top:
        box(ax, x, 72, 17, 17, "", fc=PAPER_LIGHT, ec=INK, rounded=0.5)
        label(ax, x + 8.5, 84.5, title, fs=7, bold=True)
        label(ax, x + 8.5, 77.5, body, fs=6.2, color=MUTED)
    for x in (19, 38, 57, 76):
        arrow(ax, (x, 80.5), (x + 2, 80.5))

    bottom = [
        (78, "6  Normalise", "warp to 180×180\nletterbox"),
        (59, "7  Geometry", "hull, defects,\nsolidity, extent"),
        (40, "8  Descriptors", "7 Hu + 20 Fourier\n+ 24 radial"),
        (21, "9  Classify", "StandardScaler\n+ RBF SVC"),
        (2, "10  Decide", "9-frame smoothing\n+ 1.5 s hold"),
    ]
    for x, title, body in bottom:
        box(ax, x, 38, 17, 17, "", fc="#eef4f0", ec=INK, rounded=0.5)
        label(ax, x + 8.5, 50.5, title, fs=7, bold=True)
        label(ax, x + 8.5, 43.5, body, fs=6.2, color=MUTED)
    for x in (76, 57, 38, 19):
        arrow(ax, (x, 46.5), (x - 2, 46.5))

    # wrap from top-right down into bottom-right
    arrow(ax, (86.5, 72), (86.5, 55.2), color=INK, lw=1.0)

    # output
    box(ax, 2, 8, 46, 15, "Label + confidence → transcript\n26 classes (A–Z)",
        fc="#fdf1ec", ec=ACCENT_DEEP, rounded=0.6, fs=7.2)
    arrow(ax, (10.5, 38), (10.5, 23), lw=1.0)
    save(fig, "fig_5_2_pipeline.png")


# --------------------------------------------------------------- 5.4 geometry
def geometry():
    from matplotlib.path import Path as MplPath
    from scipy.spatial import ConvexHull

    fig, ax = canvas(5.8, 5.0, 110, 100)
    pts = []
    pts += [(8, 36), (10, 48), (16, 54), (30, 57)]
    pts += [(34, 78), (38, 80), (41, 56)]
    pts += [(45, 86), (49, 86), (52, 56)]
    pts += [(56, 82), (60, 81), (62, 55)]
    pts += [(66, 72), (70, 70), (71, 53)]
    pts += [(78, 46), (78, 30), (70, 20), (40, 18), (22, 24), (12, 30)]
    poly = np.array(pts)
    ax.add_patch(Polygon(poly, closed=True, facecolor=CREAM, edgecolor=INK, lw=1.3, zorder=2))

    hull = ConvexHull(poly)
    hp = poly[hull.vertices]
    ax.add_patch(Polygon(hp, closed=True, facecolor="none", edgecolor=ACCENT,
                         lw=1.0, ls=(0, (4, 2)), zorder=3))

    x0, y0 = poly.min(axis=0)
    x1, y1 = poly.max(axis=0)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none",
                           edgecolor=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=1))

    cx, cy = poly.mean(axis=0)
    path = MplPath(poly)

    # 24 radial bins: ray from the centroid to the contour along each 15 degree step
    for ang in range(0, 360, 15):
        a = np.radians(ang)
        reach = 0.0
        for r in np.arange(2.0, 70.0, 0.5):
            if path.contains_point((cx + r * np.cos(a), cy + r * np.sin(a))):
                reach = r
        if reach:
            ax.plot([cx, cx + reach * np.cos(a)], [cy, cy + reach * np.sin(a)],
                    color=GREEN, lw=0.45, alpha=0.5, zorder=3)

    ax.plot([cx], [cy], marker="+", ms=10, color=GREEN, mew=1.6, zorder=6)
    label(ax, cx + 2.4, cy - 5.2, "centroid", fs=6.6, color=GREEN, ha="left", z=7)

    for (dx, dy) in [(41, 55), (52, 55), (62, 54), (71, 51)]:
        ax.plot([dx], [dy], marker="o", ms=4.2, color=ACCENT, zorder=7)
        ax.plot([dx, dx], [dy, dy + 8], color=ACCENT, lw=0.7, zorder=5)

    def leader(xy_from, xy_to):
        ax.plot([xy_from[0], xy_to[0]], [xy_from[1], xy_to[1]],
                color=MUTED, lw=0.5, zorder=4)

    leader((65, 75), (90, 90))
    label(ax, 91, 90, "convex hull", fs=6.8, color=ACCENT_DEEP, ha="left")

    leader((62, 54), (90, 72))
    label(ax, 91, 72, "convexity\ndefects", fs=6.8, color=ACCENT_DEEP, ha="left")

    leader((cx + 26, cy - 22), (90, 44))
    label(ax, 91, 44, "24 radial\nbins", fs=6.8, color=GREEN, ha="left")

    arrow(ax, (x0, 8), (x1, 8), style="<|-|>", color=MUTED, lw=0.6)
    label(ax, (x0 + x1) / 2, 4.4, "extent = contour area / bounding-box area", fs=6.2, color=MUTED)
    save(fig, "fig_5_4_geometry.png")


if __name__ == "__main__":
    methodology()
    conceptual()
    setup()
    architecture()
    pipeline()
    geometry()
