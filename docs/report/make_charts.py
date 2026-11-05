"""Generate the data-driven charts for the PALM/SIGN report."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
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
        "font.size": 9,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 220,
        "axes.grid": False,
    }
)

DATA = json.loads((ROOT / "model_metrics.json").read_text())
LABELS = DATA["labels"]
COUNTS = DATA["class_counts"]
PER = DATA["metrics"]["per_class"]
CM = np.array(DATA["confusion_matrix"], dtype=float)


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------------ 7.1 counts
def class_distribution() -> None:
    fig, ax = plt.subplots(figsize=(5.9, 5.1))
    y = np.arange(len(LABELS))
    values = [COUNTS[l] for l in LABELS]
    mean = float(np.mean(values))
    ax.barh(y, values, color=INK, height=0.66, edgecolor="none")
    ax.set_yticks(y, LABELS, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 440)
    ax.set_xlabel("Captured frames per sign", fontsize=8)
    ax.set_ylabel("Sign label", fontsize=8)
    for yi, v in zip(y, values):
        ax.text(v - 8, yi, str(v), va="center", ha="right", fontsize=6.6, color="white")
    ax.axvline(mean, color=ACCENT_DEEP, lw=0.9, ls=(0, (4, 2)), zorder=1)
    ax.text(mean + 6, -0.95, f"mean {mean:.0f}", fontsize=6.8, color=ACCENT_DEEP, va="center")
    ax.set_ylim(len(LABELS) - 0.4, -1.4)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2)
    save(fig, "fig_6_19_class_distribution.png")


# -------------------------------------------------------------- 7.2 accuracy
def per_sign_accuracy() -> None:
    rows = sorted(LABELS, key=lambda l: PER[l]["recall"])
    vals = [PER[l]["recall"] * 100 for l in rows]
    fig, ax = plt.subplots(figsize=(5.7, 5.4))
    y = np.arange(len(rows))
    colors = [ACCENT if v < 90 else GREEN if v >= 98 else INK for v in vals]
    ax.barh(y, vals, color=colors, height=0.68, edgecolor="none")
    ax.set_yticks(y, rows, fontsize=7)
    ax.set_xlim(80, 102)
    ax.set_xlabel("Held-out recall per sign (%)")
    ax.set_ylabel("Sign label")
    for yi, v in zip(y, vals):
        ax.text(v + 0.25, yi, f"{v:.0f}", va="center", fontsize=6.5, color=MUTED)
    ax.axvline(DATA["accuracy"] * 100, color=ACCENT_DEEP, lw=0.9, ls=(0, (4, 2)))
    ax.text(
        DATA["accuracy"] * 100 - 0.4,
        -0.9,
        f"overall {DATA['accuracy']*100:.1f}%",
        fontsize=6.5,
        color=ACCENT_DEEP,
        ha="right",
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2)
    save(fig, "fig_6_20_per_sign_recall.png")


# ------------------------------------------------------------ 7.3 confusion
def confusion() -> None:
    support = CM.sum(axis=1)
    norm = np.divide(CM, support[:, None], out=np.zeros_like(CM), where=support[:, None] > 0)
    fig, ax = plt.subplots(figsize=(6.4, 5.8))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(LABELS)), LABELS, fontsize=5.6, rotation=0)
    ax.set_yticks(np.arange(len(LABELS)), LABELS, fontsize=5.6)
    ax.set_xlabel("Predicted sign", fontsize=8)
    ax.set_ylabel("True sign", fontsize=8)
    ax.set_xticks(np.arange(-0.5, len(LABELS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.4)
    ax.tick_params(which="minor", length=0)
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            if CM[i, j] == 0:
                continue
            color = "white" if norm[i, j] > 0.55 else INK
            weight = "bold" if i == j else "normal"
            ax.text(
                j,
                i,
                f"{int(CM[i, j])}",
                ha="center",
                va="center",
                fontsize=4.6,
                color=color,
                fontweight=weight,
            )
    cbar = fig.colorbar(im, ax=ax, fraction=0.036, pad=0.02)
    cbar.set_label("Share of true class", fontsize=7)
    cbar.ax.tick_params(labelsize=6)
    save(fig, "fig_6_21_confusion_matrix.png")


# ------------------------------------------------------- 7.4 train vs test
def train_test() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.2, 2.9), gridspec_kw={"width_ratios": [1, 1.25]})
    names = ["Train", "Held-out test"]
    vals = [DATA["train_accuracy"] * 100, DATA["accuracy"] * 100]
    bars = ax1.bar(names, vals, color=[INK, GREEN], width=0.5, edgecolor="none")
    ax1.set_ylim(90, 101)
    ax1.set_ylabel("Accuracy (%)")
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.25, f"{v:.2f}%", ha="center", fontsize=8)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.tick_params(length=2)
    ax1.set_title("(a) Fit vs generalisation", fontsize=9)

    f1 = [PER[l]["f1"] * 100 for l in LABELS]
    ax2.hist(f1, bins=np.arange(80, 101, 1), color=ACCENT, edgecolor="white", linewidth=0.7)
    ax2.axvline(np.mean(f1), color=INK, lw=1, ls=(0, (4, 2)))
    ax2.set_xlabel("Per-sign F1 score (%)")
    ax2.set_ylabel("Number of signs")
    ax2.set_title("(b) Distribution of per-sign F1", fontsize=9)
    ax2.text(np.mean(f1) - 0.6, ax2.get_ylim()[1] * 0.92, f"mean {np.mean(f1):.1f}%", ha="right", fontsize=7)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.tick_params(length=2)
    save(fig, "fig_6_22_train_test.png")


# ----------------------------------------------------- 7.5 support vs recall
def support_vs_recall() -> None:
    fig, ax = plt.subplots(figsize=(4.9, 3.3))
    xs = [COUNTS[l] for l in LABELS]
    ys = [PER[l]["recall"] * 100 for l in LABELS]
    ax.scatter(xs, ys, s=26, color=INK, edgecolor="white", linewidth=0.6, zorder=3)
    for l, x, y in zip(LABELS, xs, ys):
        ax.annotate(l, (x, y), textcoords="offset points", xytext=(3, 3), fontsize=6, color=MUTED)
    z = np.polyfit(xs, ys, 1)
    grid = np.linspace(min(xs), max(xs), 50)
    ax.plot(grid, np.polyval(z, grid), color=ACCENT, lw=1, ls=(0, (4, 2)))
    r = np.corrcoef(xs, ys)[0, 1]
    ax.set_xlabel("Frames captured for the sign")
    ax.set_ylabel("Held-out recall (%)")
    ax.set_ylim(80, 102)
    ax.text(
        0.03,
        0.05,
        f"Pearson r = {r:.2f}",
        transform=ax.transAxes,
        fontsize=7.5,
        color=ACCENT_DEEP,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2)
    save(fig, "fig_6_23_support_recall.png")


# --------------------------------------------------------- 4.1 literature
def literature_timeline() -> None:
    events = [
        (2004, "K-NN +\nskin colour", "static"),
        (2012, "Deep CNN\n(ImageNet)", "deep"),
        (2016, "3-D CNN\nsign video", "deep"),
        (2019, "MediaPipe\nhands", "landmark"),
        (2021, "Transformer\nsign language", "deep"),
        (2026, "PALM/SIGN\nclassic + SVC", "ours"),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ax.axhline(0, color=INK, lw=1.2, zorder=1)
    colors = {"static": MUTED, "deep": INK, "landmark": GREEN, "ours": ACCENT}
    for i, (year, label, kind) in enumerate(events):
        x = i
        ax.plot([x], [0], marker="o", ms=7, color=colors[kind], zorder=3,
                markeredgecolor="white", markeredgewidth=1)
        va = "bottom" if i % 2 == 0 else "top"
        off = 0.18 if i % 2 == 0 else -0.18
        ax.text(x, off, str(year), ha="center", va=va, fontsize=7.5,
                fontweight="bold", color=colors[kind])
        ax.text(x, off * 2.4, label, ha="center", va=va, fontsize=6.8, color=INK)
    ax.set_xlim(-0.6, len(events) - 0.4)
    ax.set_ylim(-1.15, 1.15)
    ax.axis("off")
    save(fig, "fig_4_1_literature_timeline.png")


# --------------------------------------------------------------- 6.10 gantt
def gantt() -> None:
    tasks = [
        ("Problem study & literature", 0, 2),
        ("Data collection (A-Z)", 1.5, 3.5),
        ("Segmentation pipeline", 2.5, 2.5),
        ("Feature engineering", 3.5, 2.5),
        ("Classifier training", 5, 2),
        ("Web workbench (Flask)", 5.5, 3),
        ("Testing & tuning", 7.5, 2.5),
        ("Report writing", 8, 3),
    ]
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    for i, (name, start, dur) in enumerate(tasks):
        ax.barh(i, dur, left=start, height=0.52,
                color=ACCENT if i % 2 else INK, edgecolor="none")
        ax.text(start + dur + 0.1, i, f"w{int(start+1)}-{int(start+dur)}",
                va="center", fontsize=6, color=MUTED)
    ax.set_yticks(range(len(tasks)), [t[0] for t in tasks], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 12)
    ax.set_xticks(range(0, 12, 2), [f"W{i}" for i in range(0, 12, 2)])
    ax.set_xlabel("Project week")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2)
    ax.grid(axis="x", color=LINE, lw=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    save(fig, "fig_6_5_gantt.png")


# ------------------------------------------------------- 5.x feature split
def feature_split() -> None:
    parts = [("Geometry", 10, INK), ("Hu moments", 7, GREEN),
             ("Fourier", 20, ACCENT), ("Radial", 24, MUTED)]
    fig, ax = plt.subplots(figsize=(5.6, 1.25))
    left = 0
    for name, size, color in parts:
        ax.barh(0, size, left=left, height=0.5, color=color, edgecolor="white", linewidth=1)
        ax.text(left + size / 2, 0, f"{name}\n{size}", ha="center", va="center",
                fontsize=7, color="white", fontweight="bold")
        left += size
    ax.set_xlim(0, 61)
    ax.set_ylim(-0.6, 0.6)
    ax.axis("off")
    ax.text(61.4, 0, "61-D", va="center", fontsize=8, color=INK, fontweight="bold")
    save(fig, "fig_5_3_feature_split.png")


if __name__ == "__main__":
    class_distribution()
    per_sign_accuracy()
    confusion()
    train_test()
    support_vs_recall()
    literature_timeline()
    gantt()
    feature_split()
