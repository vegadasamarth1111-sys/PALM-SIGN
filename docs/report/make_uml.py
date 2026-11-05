"""Generate the UML and process diagrams for the PALM/SIGN report."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_diagrams import (  # noqa: E402
    ACCENT,
    ACCENT_DEEP,
    CREAM,
    FIG,
    GREEN,
    INK,
    LINE,
    MUTED,
    PAPER_DEEP,
    PAPER_LIGHT,
    arrow,
    box,
    canvas,
    label,
    save,
)


def actor(ax, x, y, name, fs=7):
    ax.add_patch(Circle((x, y + 8), 1.7, facecolor="white", edgecolor=INK, lw=1.0, zorder=3))
    ax.plot([x, x], [y + 6.3, y + 1.5], color=INK, lw=1.0, zorder=3)
    ax.plot([x - 3.4, x + 3.4], [y + 4.6, y + 4.6], color=INK, lw=1.0, zorder=3)
    ax.plot([x, x - 2.6], [y + 1.5, y - 2.6], color=INK, lw=1.0, zorder=3)
    ax.plot([x, x + 2.6], [y + 1.5, y - 2.6], color=INK, lw=1.0, zorder=3)
    label(ax, x, y - 5.2, name, fs=fs, color=INK, bold=True)


def oval(ax, x, y, w, h, text, fs=6.8, fc="white"):
    ax.add_patch(Ellipse((x, y), w, h, facecolor=fc, edgecolor=INK, lw=0.9, zorder=2))
    label(ax, x, y, text, fs=fs, color=INK)


def diamond(ax, x, y, w, h, text, fs=6.6):
    ax.add_patch(Polygon([(x, y + h), (x + w, y), (x, y - h), (x - w, y)],
                         closed=True, facecolor="#fdf1ec", edgecolor=ACCENT_DEEP, lw=1.0, zorder=2))
    label(ax, x, y, text, fs=fs, color=INK)


def uml_class(ax, x, y, w, h, name, attrs=(), methods=(), fs=6.2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=INK, lw=1.0, zorder=2))
    head = 5.2
    ax.plot([x, x + w], [y + h - head, y + h - head], color=INK, lw=0.8, zorder=3)
    label(ax, x + w / 2, y + h - head / 2, name, fs=fs + 0.8, color=INK, bold=True)
    ay = y + h - head - 2.2
    for a in attrs:
        label(ax, x + 1.4, ay, a, fs=fs, color=MUTED, ha="left")
        ay -= 2.4
    if attrs and methods:
        ax.plot([x, x + w], [ay + 1.0, ay + 1.0], color=LINE, lw=0.6, zorder=3)
        ay -= 1.0
    for m in methods:
        label(ax, x + 1.4, ay, m, fs=fs, color=INK, ha="left")
        ay -= 2.4


# --------------------------------------------------------------- 6.1 paradigm
def paradigm():
    fig, ax = canvas(6.2, 5.0, ymax=100)
    phases = [
        (50, 88, "Requirements"),
        (77, 68, "Design"),
        (50, 48, "Implementation"),
        (23, 68, "Testing"),
    ]
    for x, y, text in phases:
        box(ax, x - 11, y - 5, 22, 10, text, fc=PAPER_LIGHT, rounded=0.8, fs=7.4)
    arrow(ax, (61, 86), (68, 73), rad=-0.15)
    arrow(ax, (72, 63), (61, 51), rad=-0.15)
    arrow(ax, (39, 51), (28, 63), rad=-0.15)
    arrow(ax, (32, 73), (39, 86), rad=-0.15)
    label(ax, 50, 68, "iteration\nn → n+1", fs=6.6, color=ACCENT_DEEP, bold=True)

    label(ax, 50, 36, "Deliverable grows with each increment", fs=6.8, color=MUTED, style="italic")
    incs = [
        (4, "I1", "Camera loop\n+ segmentation"),
        (28, "I2", "Features +\nSVC model"),
        (52, "I3", "Live desk\n+ transcript"),
        (76, "I4", "Capture, train,\nreset, metrics"),
    ]
    for x, tag, text in incs:
        box(ax, x, 12, 20, 16, "", fc="#eef4f0", rounded=0.5)
        label(ax, x + 10, 24, tag, fs=8, color=GREEN, bold=True)
        label(ax, x + 10, 17.5, text, fs=6.0, color=MUTED)
    for x in (24, 48, 72):
        arrow(ax, (x, 20), (x + 4, 20), ms=6)
    save(fig, "fig_6_1_paradigm.png")


# ---------------------------------------------------------------- 6.2 use case
def usecase():
    fig, ax = canvas(6.4, 5.6)
    ax.add_patch(Rectangle((22, 3), 56, 90, facecolor="none", edgecolor=INK, lw=1.0, ls=(0, (5, 3))))
    label(ax, 50, 97, "PALM/SIGN workbench", fs=8, color=INK, bold=True)

    actor(ax, 8, 47, "User")
    actor(ax, 92, 47, "Webcam")

    rows = [
        (87, "Open workbench"),
        (77, "View live reading"),
        (67, "Switch input mode"),
        (57, "Tune skin range"),
        (47, "Inspect pipeline stages"),
        (37, "Clear transcript"),
        (27, "Capture sign frames"),
        (17, "Train model"),
        (7, "Reset lab"),
    ]
    for y, text in rows:
        oval(ax, 51, y, 38, 8, text)
    for y, _ in rows:
        arrow(ax, (11.5, 51), (32, y), lw=0.6, ms=5, rad=0.03)

    # the camera participates in only two use cases
    arrow(ax, (88.5, 55), (70, 77), lw=0.7, ms=5, rad=-0.1)
    arrow(ax, (88.5, 55), (70, 27), lw=0.7, ms=5, rad=0.1)
    save(fig, "fig_6_2_usecase.png")


# ---------------------------------------------------------------- 6.3 activity
def activity():
    fig, ax = canvas(5.4, 6.1, equal=False)
    cx = 34
    W = 46

    ax.add_patch(Circle((cx, 96), 1.7, facecolor=INK, edgecolor=INK, zorder=3))
    box(ax, cx - W / 2, 85, W, 6, "Open the workbench in a browser", fc=PAPER_LIGHT, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 94.3), (cx, 91))

    box(ax, cx - W / 2, 76, W, 6, "Start camera thread (30 fps)", fc=PAPER_LIGHT, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 85), (cx, 82))

    box(ax, cx - W / 2, 67, W, 6, "Capture next frame", fc=PAPER_LIGHT, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 76), (cx, 73))

    diamond(ax, cx, 58, 18, 7, "Hand inside\nROI?")
    arrow(ax, (cx, 67), (cx, 61.5))

    box(ax, cx - W / 2, 44, W, 7, "Normalise + extract 61-D vector", fc=PAPER_LIGHT, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 54.5), (cx, 51))
    label(ax, cx + 4.2, 52.4, "yes", fs=6.2, color=GREEN, bold=True, ha="left", bg="white")

    box(ax, cx - W / 2, 34, W, 6, "SVC classify \u2192 label, probability", fc=PAPER_LIGHT, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 44), (cx, 40))

    diamond(ax, cx, 24, 20, 7, "p \u2265 0.55 and\nheld 1.5 s?")
    arrow(ax, (cx, 34), (cx, 27.5))

    box(ax, cx - W / 2, 8, W, 6.4, "Append letter, update transcript", fc=CREAM, rounded=0.5, fs=7.2)
    arrow(ax, (cx, 20.5), (cx, 14.4))
    label(ax, cx + 4.2, 17.0, "yes", fs=6.2, color=GREEN, bold=True, ha="left", bg="white")

    # three paths merge into one return trunk on the right
    trunk = 86
    ax.plot([trunk, trunk], [4.8, 70], color=INK, lw=0.8, zorder=1)
    arrow(ax, (trunk, 70), (cx + W / 2, 70), lw=0.8)

    ax.plot([cx + 18, trunk], [58, 58], color=ACCENT_DEEP, lw=0.8, ls=(0, (3, 2)))
    label(ax, cx + 19.5, 59.8, "no \u2014 keep searching", fs=6.0, color=ACCENT_DEEP, ha="left", bg="white")

    ax.plot([cx + 20, trunk], [24, 24], color=ACCENT_DEEP, lw=0.8, ls=(0, (3, 2)))
    label(ax, cx + 21.5, 25.8, "no \u2014 keep reading", fs=6.0, color=ACCENT_DEEP, ha="left", bg="white")

    ax.plot([cx, cx], [8, 4.8], color=INK, lw=0.8)
    ax.plot([cx, trunk], [4.8, 4.8], color=INK, lw=0.8)
    label(ax, cx + 22, 3.0, "after a commit, keep reading", fs=5.8, color=MUTED, ha="center")

    save(fig, "fig_6_3_activity.png")


# --------------------------------------------------------- 6.4 sequence live
def sequence_live():
    fig, ax = canvas(6.4, 4.6, equal=False)
    xs = [10, 32, 53, 74, 92]
    names = ["Browser", "Flask\n/api/state", "VisionEngine", "Segmenter", "Classifier"]
    for x, n in zip(xs, names):
        box(ax, x - 8, 84, 16, 9, n, fc=PAPER_LIGHT, rounded=0.3, fs=6.4)
        ax.plot([x, x], [6, 84], color=LINE, lw=0.7, ls=(0, (4, 3)))
    label(ax, 50, 97, "Live recognition loop (polled twice per second)", fs=7.4, color=INK, bold=True)

    def msg(y, i, j, text, dashed=False, ret=False, fs=5.9):
        x1, x2 = xs[i], xs[j]
        ax.plot([x1, x1], [y + 1, y - 1], color=INK, lw=2.2, zorder=4)
        ax.plot([x2, x2], [y + 1, y - 1], color=INK, lw=2.2, zorder=4)
        arrow(ax, (x1, y), (x2, y), style="-|>", lw=0.8, ms=6,
              ls=(0, (3, 2)) if dashed else "-")
        label(ax, (x1 + x2) / 2, y + 2.4, text, fs=fs, color=INK if not ret else MUTED,
              style="italic" if ret else "normal")

    msg(80, 0, 1, "GET /api/state")
    msg(72, 1, 2, "snapshot()")
    msg(64, 2, 3, "analyse(frame)")
    msg(56, 3, 2, "mask, contour, hull", dashed=True, ret=True)
    msg(48, 2, 4, "predict(vector)")
    msg(40, 4, 2, "label, probability", dashed=True, ret=True)
    msg(32, 2, 1, "state dict", dashed=True, ret=True)
    msg(24, 1, 0, "JSON", dashed=True, ret=True)
    msg(14, 0, 1, "GET /video_feed")
    msg(8, 1, 0, "MJPEG frames", dashed=True, ret=True)
    save(fig, "fig_6_4_sequence_live.png")


# ------------------------------------------------------ 6.5 sequence capture
def sequence_capture():
    fig, ax = canvas(6.4, 5.6, equal=False)
    xs = [9, 30, 50, 70, 91]
    names = ["Browser", "Flask\n/api/collect", "VisionEngine", "Dataset", "Classifier"]
    for x, n in zip(xs, names):
        box(ax, x - 8, 86, 16, 8, n, fc=PAPER_LIGHT, rounded=0.3, fs=6.3)
        ax.plot([x, x], [4, 86], color=LINE, lw=0.7, ls=(0, (4, 3)))
    label(ax, 50, 99, "Capture, train and reset", fs=7.4, color=INK, bold=True)

    def msg(y, i, j, text, dashed=False, ret=False, fs=5.8):
        x1, x2 = xs[i], xs[j]
        ax.plot([x1, x1], [y + 1, y - 1], color=INK, lw=2.2, zorder=4)
        ax.plot([x2, x2], [y + 1, y - 1], color=INK, lw=2.2, zorder=4)
        arrow(ax, (x1, y), (x2, y), style="-|>", lw=0.8, ms=6,
              ls=(0, (3, 2)) if dashed else "-")
        label(ax, (x1 + x2) / 2, y + 2.3, text, fs=fs, color=INK if not ret else MUTED,
              style="italic" if ret else "normal")

    msg(82, 0, 1, "POST /api/collect {start}")
    msg(75, 1, 2, "start_collection(label, n)")
    msg(68, 2, 3, "append_features(label, vector)  × n frames")
    msg(61, 2, 1, "have, target, progress", dashed=True, ret=True)
    msg(54, 1, 0, "collect state", dashed=True, ret=True)
    msg(46, 0, 1, "POST /api/train")
    msg(39, 1, 4, "train_model()")
    msg(32, 4, 3, "load_training_data()")
    msg(25, 3, 4, "X, y", dashed=True, ret=True)
    msg(18, 4, 1, "report, accuracy", dashed=True, ret=True)
    msg(11, 1, 0, "metrics JSON", dashed=True, ret=True)
    msg(5, 0, 1, "POST /api/reset {confirm}", fs=5.4)
    save(fig, "fig_6_5_sequence_capture.png")


# ----------------------------------------------------------------- 6.6 class
def class_diagram():
    fig, ax = canvas(6.4, 5.4, equal=False)
    uml_class(ax, 2, 74, 30, 20, "Flask App",
              ["+ routes, engine"],
              ["+ /api/state", "+ /api/collect /api/train"], fs=5.8)
    uml_class(ax, 2, 42, 30, 26, "VisionEngine",
              ["- lock, fps, frame_seq", "- model_bundle, text"],
              ["+ start()", "+ snapshot()", "+ start_collection()"], fs=5.8)
    uml_class(ax, 2, 10, 30, 24, "Dataset",
              ["+ label_dir(label)", "+ feature arrays"],
              ["+ append_features()", "+ load_training_data()"], fs=5.8)

    uml_class(ax, 36, 74, 28, 20, "Segmentation",
              ["+ mask, hand, hull", "+ defects"],
              ["+ analyse(frame)"], fs=5.8)
    uml_class(ax, 36, 42, 28, 24, "HandFeatures",
              ["+ vector: ndarray[61]", "+ info: dict"],
              ["+ extract_features()"], fs=5.8)
    uml_class(ax, 36, 10, 28, 24, "MotionTracker",
              ["+ previous frame", "+ history deque"],
              ["+ update(gray, bbox)"], fs=5.8)

    uml_class(ax, 68, 56, 30, 26, "Classifier",
              ["+ pipeline: Scaler+SVC"],
              ["+ train_model()", "+ predict(vector)", "+ load_model()"], fs=5.8)
    uml_class(ax, 68, 26, 30, 22, "ModelBundle",
              ["+ accuracy, labels", "+ confusion_matrix"],
              ["+ save() / load()"], fs=5.8)

    arrow(ax, (17, 74), (17, 68), style="-|>", lw=0.8, ms=6)
    arrow(ax, (17, 42), (17, 34), style="-|>", lw=0.8, ms=6)
    arrow(ax, (32, 84), (36, 84), style="-|>", lw=0.8, ms=6)
    arrow(ax, (50, 74), (50, 66), style="-|>", lw=0.8, ms=6)
    arrow(ax, (32, 55), (36, 30), style="-|>", lw=0.8, ms=6, ls=(0, (3, 2)))
    label(ax, 31, 40, "motion", fs=5.2, color=MUTED, ha="right")
    arrow(ax, (64, 54), (68, 66), style="-|>", lw=0.8, ms=6)
    label(ax, 65, 62, "vector", fs=5.2, color=MUTED, ha="left")
    arrow(ax, (83, 56), (83, 48), style="-|>", lw=0.8, ms=6)
    label(ax, 84.5, 52, "save", fs=5.2, color=MUTED, ha="left")
    save(fig, "fig_6_6_class.png")


# ----------------------------------------------------------------- 6.7 state
def state_diagram():
    fig, ax = canvas(6.2, 4.4)
    ax.add_patch(Circle((3, 81), 1.6, facecolor=INK, edgecolor=INK))
    states = [
        (8, 76, 15, 10, "Idle"),
        (27, 76, 15, 10, "Starting"),
        (46, 76, 15, 10, "Streaming"),
        (65, 76, 15, 10, "Reading"),
        (84, 76, 15, 10, "Committed"),
        (30, 42, 18, 10, "Collecting"),
        (58, 42, 18, 10, "Training"),
        (8, 14, 20, 10, "Error"),
    ]
    for x, y, w, h, text in states:
        box(ax, x, y, w, h, text, fc=PAPER_LIGHT, rounded=1.2, fs=6.8)

    arrow(ax, (4.6, 81), (8, 81), ms=6)
    arrow(ax, (23, 81), (27, 81), ms=6)
    arrow(ax, (42, 81), (46, 81), ms=6)
    arrow(ax, (61, 81), (65, 81), ms=6)
    label(ax, 63, 88.5, "hand", fs=5.2, color=MUTED)
    arrow(ax, (80, 81), (84, 81), ms=6)
    label(ax, 82, 88.5, "1.5 s", fs=5.2, color=MUTED)

    # committed self loop
    ax.add_patch(FancyArrowPatch((89, 86), (95, 86), connectionstyle="arc3,rad=-1.4",
                                 arrowstyle="-|>", mutation_scale=6, color=INK, lw=0.8))
    label(ax, 92, 92, "next sign", fs=5.2, color=MUTED)

    # capture -> training
    arrow(ax, (48, 76), (40, 52), ms=6, rad=0.15)
    label(ax, 41, 63, "start\ncapture", fs=5.2, color=MUTED, ha="right")
    arrow(ax, (48, 47), (58, 47), ms=6)
    label(ax, 53, 49.2, "target", fs=5.2, color=MUTED)
    arrow(ax, (72, 52), (55, 76), ms=6, rad=-0.45, ls=(0, (3, 2)))
    label(ax, 70, 60, "model\nreloaded", fs=5.2, color=MUTED)

    # camera failure
    arrow(ax, (27, 76), (16, 24), ms=6, color=ACCENT_DEEP, rad=0.12, ls=(0, (3, 2)))
    label(ax, 19, 47, "camera\nfailure", fs=5.2, color=ACCENT_DEEP, ha="left", bg="white")
    save(fig, "fig_6_7_state.png")


# ------------------------------------------------------------ 6.8 deployment
def deployment():
    fig, ax = canvas(6.4, 3.6, equal=False)
    # browser node
    box(ax, 2, 26, 26, 48, "", fc=PAPER_LIGHT, ec=INK, rounded=0.4)
    label(ax, 15, 70, "«device»", fs=5.8, color=MUTED, style="italic")
    label(ax, 15, 65, "User browser", fs=7.2, bold=True)
    box(ax, 5, 48, 20, 13, "index.html\napp.js\nstyle.css", fc="white", fs=5.6)
    box(ax, 5, 38, 20, 7, "HTTP client", fc="white", fs=5.6)

    # server node
    box(ax, 34, 4, 34, 90, "", fc="#eef4f0", ec=INK, rounded=0.4)
    label(ax, 51, 90, "«server»", fs=5.8, color=MUTED, style="italic")
    label(ax, 51, 85, "Host PC (localhost)", fs=7.2, bold=True)
    box(ax, 37, 70, 28, 10, "Flask app.py\nroutes + /video_feed", fc="white", fs=5.6)
    box(ax, 37, 56, 28, 9, "VisionEngine thread", fc="white", fs=5.6)
    box(ax, 37, 42, 28, 10, "sign_model.joblib\nScaler + RBF SVC", fc="white", fs=5.6)
    box(ax, 37, 28, 28, 10, "dataset/<SIGN>/*.npy\n6,983 frames", fc="white", fs=5.6)

    # webcam node
    box(ax, 74, 40, 24, 34, "", fc=PAPER_LIGHT, ec=INK, rounded=0.4)
    label(ax, 86, 68, "«device»", fs=5.8, color=MUTED, style="italic")
    label(ax, 86, 63, "USB webcam", fs=7.0, bold=True)
    box(ax, 77, 48, 18, 10, "OpenCV\nVideoCapture", fc="white", fs=5.6)

    # connections
    ax.plot([28, 34], [50, 50], color=INK, lw=1.0)
    label(ax, 31, 53.5, "HTTP\nlocalhost", fs=5.0, color=MUTED, bg="white")
    ax.plot([68, 74], [50, 50], color=INK, lw=1.0)
    label(ax, 71, 53.5, "USB", fs=5.0, color=MUTED, bg="white")
    save(fig, "fig_6_8_deployment.png")


# ------------------------------------------------------------- 6.9 component
def component():
    fig, ax = canvas(6.3, 4.8, equal=False)
    groups = [
        (2, "Frontend", ["index.html", "app.js", "style.css"], PAPER_LIGHT),
        (27, "Application", ["app.py", "engine.py"], "#eef4f0"),
        (52, "Vision", ["segment.py", "features.py", "motion.py", "preprocess.py"], "#eef4f0"),
        (77, "Model & data", ["classifier.py", "dataset.py", "sign_model.joblib", "dataset/*.npy"], "#fdf1ec"),
    ]
    for x, title, items, fc in groups:
        box(ax, x, 10, 21, 78, "", fc="white", ec=LINE, rounded=0.3, ls=(0, (3, 2)))
        label(ax, x + 10.5, 84, title, fs=7.2, color=INK, bold=True)
        y = 72
        for item in items:
            box(ax, x + 1.5, y, 18, 8, item, fc=fc, fs=6.0, rounded=0.25)
            ax.add_patch(Rectangle((x + 1.5, y), 2.2, 8, facecolor="none", edgecolor=INK, lw=0.5))
            ax.plot([x + 3.7, x + 3.7], [y + 2, y + 6], color=INK, lw=0.5)
            y -= 11
    for x in (23, 48, 73):
        arrow(ax, (x, 50), (x + 4, 50), style="<|-|>", ms=6, lw=0.8)
    label(ax, 50, 4, "All Python components run inside one Flask process; data components are files on disk.",
          fs=6.0, color=MUTED, style="italic")
    save(fig, "fig_6_9_component.png")




# --------------------------------------------------------- 6.8 collaboration
def collaboration():
    fig, ax = canvas(6.3, 4.3, equal=False)

    def obj(x, y, w, h, name, cls, attrs=()):
        box(ax, x, y, w, h, "", fc=PAPER_LIGHT, ec=INK, rounded=0.3)
        label(ax, x + w / 2, y + h - 3.4, f"{name} : {cls}", fs=6.4, bold=True)
        ax.plot([x, x + w], [y + h - 6.6, y + h - 6.6], color=INK, lw=0.6)
        yy = y + h - 9.6
        for a in attrs:
            label(ax, x + w / 2, yy, a, fs=5.6, color=MUTED)
            yy -= 3.4

    obj(2, 62, 27, 26, "ui", "Browser", ["poll 500 ms", "render state"])
    obj(36.5, 62, 27, 26, "app", "Flask App", ["/api/state", "/video_feed"])
    obj(71, 62, 27, 26, "engine", "VisionEngine", ["worker thread", "state lock"])
    obj(71, 18, 27, 26, "seg", "SkinSegmenter", ["HSV bounds", "face cascade"])
    obj(36.5, 18, 27, 26, "clf", "Classifier", ["Scaler + SVC"])
    obj(2, 18, 27, 26, "data", "Dataset", ["26 label dirs", "features.npy"])

    # links
    ax.plot([29, 36.5], [75, 75], color=INK, lw=0.9)
    ax.plot([63.5, 71], [75, 75], color=INK, lw=0.9)
    ax.plot([84.5, 84.5], [62, 44], color=INK, lw=0.9)
    ax.plot([71, 63.5], [31, 31], color=INK, lw=0.9)
    ax.plot([36.5, 29], [31, 31], color=INK, lw=0.9)
    ax.plot([50, 50], [62, 44], color=INK, lw=0.9)

    label(ax, 32.7, 77.2, "1", fs=6.0, color=ACCENT_DEEP, bold=True, bg="white")
    label(ax, 67.2, 77.2, "2", fs=6.0, color=ACCENT_DEEP, bold=True, bg="white")
    label(ax, 84.5, 53, "3", fs=6.0, color=ACCENT_DEEP, bold=True, rot=90, bg="white")
    label(ax, 67.2, 33.2, "4", fs=6.0, color=ACCENT_DEEP, bold=True, bg="white")
    label(ax, 32.7, 33.2, "5", fs=6.0, color=ACCENT_DEEP, bold=True, bg="white")
    label(ax, 51.6, 53, "2.1", fs=5.4, color=MUTED, rot=90, style="italic", bg="white")
    label(ax, 50, 5, "1 state()   2 snapshot()   2.1 state   3 analyse()   4 predict()   5 append()",
          fs=5.6, color=MUTED)
    save(fig, "fig_6_8_collaboration.png")


# --------------------------------------------------------------- 6.11 object
def object_diagram():
    fig, ax = canvas(6.4, 3.7, equal=False)

    def inst(x, y, w, h, title, rows):
        box(ax, x, y, w, h, "", fc="white", ec=INK, rounded=0.2)
        label(ax, x + w / 2, y + h - 3.6, title, fs=6.3, bold=True)
        ax.plot([x, x + w], [y + h - 6.8, y + h - 6.8], color=INK, lw=0.6)
        yy = y + h - 9.8
        for r in rows:
            label(ax, x + w / 2, yy, r, fs=5.4, color=MUTED)
            yy -= 3.2

    inst(2, 58, 30, 30, "e : VisionEngine", ["fps = 29.5", "text = ''", "commits = 0", "mode = 'model'"])
    inst(36, 58, 30, 30, "b : ModelBundle", ["labels = A..Z (26)", "accuracy = 0.9771", "samples = 6983"])
    inst(70, 58, 28, 30, "s : Segmentation", ["hand = contour", "defects = 2", "faces = 1"])

    inst(2, 14, 30, 26, "d : Dataset", ["labels = 26", "files = 6,983"])
    inst(36, 14, 30, 26, "f : HandFeatures", ["vector[61]", "solidity = 0.91"])
    inst(70, 14, 28, 26, "c : Classifier", ["C = 8", "gamma = 'scale'"])

    ax.plot([17, 17], [58, 40], color=INK, lw=0.9)
    ax.plot([51, 51], [58, 40], color=INK, lw=0.9)
    ax.plot([84, 84], [58, 40], color=INK, lw=0.9)
    ax.plot([32, 36], [73, 73], color=INK, lw=0.9)
    ax.plot([66, 70], [73, 73], color=INK, lw=0.9)
    ax.plot([32, 36], [27, 27], color=INK, lw=0.9)
    ax.plot([66, 70], [27, 27], color=INK, lw=0.9)

    label(ax, 50, 5, "Snapshot taken while the desk is reading; values match the live run in Figure 6.14.",
          fs=5.6, color=MUTED, style="italic")
    save(fig, "fig_6_11_object.png")


# ----------------------------------------------------- 6.10 lab activity
def activity_lab():
    fig, ax = canvas(5.0, 6.6, equal=False)
    cx = 50
    W = 58

    ax.add_patch(Circle((cx, 97), 1.7, facecolor=INK, edgecolor=INK, zorder=3))
    box(ax, cx - W / 2, 88, W, 6, "Open the lab panel", fc=PAPER_LIGHT, rounded=0.5, fs=7.0)
    arrow(ax, (cx, 95.3), (cx, 94))

    box(ax, cx - W / 2, 79, W, 6, "Choose sign label and frame target", fc=PAPER_LIGHT, rounded=0.5, fs=7.0)
    arrow(ax, (cx, 88), (cx, 85))

    box(ax, cx - W / 2, 70, W, 6, "Start capture", fc=PAPER_LIGHT, rounded=0.5, fs=7.0)
    arrow(ax, (cx, 79), (cx, 76))

    diamond(ax, cx, 60, 18, 6.5, "Hand found in\nthis frame?")
    arrow(ax, (cx, 70), (cx, 66.5))

    box(ax, cx - W / 2, 45, W, 6, "Extract 61-D vector, append to dataset", fc=PAPER_LIGHT, rounded=0.5, fs=7.0)
    arrow(ax, (cx, 53.5), (cx, 51))
    label(ax, cx + 2.4, 52.2, "yes", fs=5.8, color=GREEN, bold=True, ha="left", bg="white")

    diamond(ax, cx, 35, 16, 6, "Target\nreached?")
    arrow(ax, (cx, 45), (cx, 41))

    box(ax, cx - W / 2, 21, W, 6, "Train model on all stored features", fc="#eef4f0", rounded=0.5, fs=7.0)
    arrow(ax, (cx, 29), (cx, 27))
    label(ax, cx + 2.4, 28, "yes", fs=5.8, color=GREEN, bold=True, ha="left", bg="white")

    box(ax, cx - W / 2, 8, W, 6, "Reload model and refresh metrics", fc=CREAM, rounded=0.5, fs=7.0)
    arrow(ax, (cx, 21), (cx, 14))

    # no-hand branch loops back to capture
    ax.plot([cx + 18, 90, 90], [60, 60, 73], color=ACCENT_DEEP, lw=0.8, ls=(0, (3, 2)))
    arrow(ax, (90, 73), (cx + W / 2, 73), color=ACCENT_DEEP, lw=0.8, ls=(0, (3, 2)))
    label(ax, 88, 56.5, "no ? skip frame", fs=5.6, color=ACCENT_DEEP, ha="right", bg="white")

    # target not reached loops back to capture
    ax.plot([cx - 16, 12, 12], [35, 35, 73], color=INK, lw=0.8)
    arrow(ax, (12, 73), (cx - W / 2, 73), lw=0.8)
    label(ax, 15, 52, "no ? next\nframe", fs=5.4, color=MUTED, ha="left")
    save(fig, "fig_6_10_activity_lab.png")

if __name__ == "__main__":
    paradigm()
    usecase()
    activity()
    sequence_live()
    sequence_capture()
    class_diagram()
    state_diagram()
    deployment()
    component()
    collaboration()
    object_diagram()
    activity_lab()
