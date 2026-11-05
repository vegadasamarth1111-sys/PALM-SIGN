"""Build the PALM / SIGN project presentation.

The deck follows the visual grammar of the reference deck (dark ground, single
accent, numbered section kickers, hairline footer) but is rebuilt from scratch
around this project's own material: real masks, real metrics and real
screenshots taken from the running workbench.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
OUT = ROOT.parent.parent / "PALM_SIGN_Presentation.pptx"

# ------------------------------------------------------------------ palette
BG = RGBColor(0x0A, 0x15, 0x24)
PANEL = RGBColor(0x13, 0x23, 0x3A)
PANEL2 = RGBColor(0x1B, 0x2E, 0x49)
RULE = RGBColor(0x1E, 0x30, 0x49)
TEXT = RGBColor(0xF7, 0xF9, 0xFC)
MUTED = RGBColor(0x8F, 0xA1, 0xB9)
ACCENT = RGBColor(0xE6, 0x53, 0x2F)
ACCENT_L = RGBColor(0xF5, 0x8A, 0x6A)
CREAM = RGBColor(0xF4, 0xED, 0xE1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x11, 0x1A, 0x26)
GREY = RGBColor(0x5B, 0x6B, 0x80)
GREEN = RGBColor(0x3F, 0x8F, 0x6B)
PLATE_LINE = RGBColor(0xDC, 0xE4, 0xEE)

BODY = "Segoe UI"
LIGHT = "Segoe UI Light"

W, H = 13.333, 7.5
TOTAL = 19


# ------------------------------------------------------------------ helpers
def I(v: float) -> Inches:
    return Inches(v)


def rect(slide, x, y, w, h, fill=None, line=None, lw=0.75, radius=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius is not None else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(kind, I(x), I(y), I(w), I(h))
    if radius is not None:
        sh.adjustments[0] = radius
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    return sh


def _apply(run, size, color, bold, font, spc, caps, italic=False):
    f = run.font
    f.name = font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    if spc:
        rpr.set("spc", str(int(spc * 100)))
    if caps:
        rpr.set("cap", "all")


def _runs(p, runs, size, color, bold, font, spc, caps, italic=False):
    if isinstance(runs, str):
        runs = [(runs, {})]
    for txt, opt in runs:
        run = p.add_run()
        run.text = txt
        _apply(
            run,
            opt.get("size", size),
            opt.get("color", color),
            opt.get("bold", bold),
            opt.get("font", font),
            opt.get("spc", spc),
            opt.get("caps", caps),
            opt.get("italic", italic),
        )


def _bullet(p, char="•", color=ACCENT, marL=0.24, indent=-0.24):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(I(marL))))
    pPr.set("indent", str(int(I(indent))))
    from lxml import etree

    ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    for tag in ("buClr", "buSzPct", "buFont", "buChar", "buNone"):
        for el in pPr.findall(qn("a:" + tag)):
            pPr.remove(el)
    buClr = etree.SubElement(pPr, qn("a:buClr"))
    clr = etree.SubElement(buClr, qn("a:srgbClr"))
    clr.set("val", "%02X%02X%02X" % (color[0], color[1], color[2]))
    buSz = etree.SubElement(pPr, qn("a:buSzPct"))
    buSz.set("val", "100000")
    buFont = etree.SubElement(pPr, qn("a:buFont"))
    buFont.set("typeface", "Arial")
    buChar = etree.SubElement(pPr, qn("a:buChar"))
    buChar.set("char", char)
    _ = ns


def block(
    slide,
    x,
    y,
    w,
    h,
    items,
    size=13,
    color=TEXT,
    font=BODY,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line=1.12,
    spc=None,
    caps=False,
    bold=False,
    italic=False,
):
    """A text box holding one or more paragraphs.

    Each item is a dict with ``text`` (str or list of runs) plus optional
    ``size``, ``color``, ``bold``, ``before``, ``after``, ``bullet``, ``line``.
    """
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = item.get("align", align)
        _runs(
            p,
            item["text"],
            item.get("size", size),
            item.get("color", color),
            item.get("bold", bold),
            item.get("font", font),
            item.get("spc", spc),
            item.get("caps", caps),
            item.get("italic", italic),
        )
        if item.get("bullet"):
            _bullet(p, color=item.get("bullet_color", ACCENT))
        p.line_spacing = item.get("line", line)
        p.space_before = Pt(item.get("before", 0))
        p.space_after = Pt(item.get("after", 0))
    return tb


def fit(slide, name, x, y, w, h, border=None):
    path = FIG / name
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    left = x + (w - pw) / 2
    top = y + (h - ph) / 2
    pic = slide.shapes.add_picture(str(path), I(left), I(top), I(pw), I(ph))
    if border:
        pic.line.color.rgb = border
        pic.line.width = Pt(0.75)
    return pic


def plate(slide, name, x, y, w, h, caption=None, pad=0.18):
    """A white figure plate, with an optional caption set inside it."""
    rect(slide, x, y, w, h, fill=WHITE, line=PLATE_LINE, lw=0.75, radius=0.025)
    cap_h = 0.30 if caption else 0.0
    fit(slide, name, x + pad, y + pad, w - 2 * pad, h - 2 * pad - cap_h)
    if caption:
        block(
            slide,
            x + pad,
            y + h - pad - cap_h + 0.02,
            w - 2 * pad,
            cap_h,
            [{"text": caption}],
            size=8,
            color=GREY,
            line=1.0,
        )


def chrome(slide, idx, section, title, lede=None):
    """Shared header, progress rail and footer for a content slide."""
    rect(slide, 0, 0, W, H, fill=BG)
    # progress ticks: one mark per slide, the current one in accent
    for i in range(TOTAL):
        ty = 1.72 + i * 0.226
        if i == idx:
            colour = ACCENT
        elif i < idx:
            colour = RGBColor(0x33, 0x46, 0x60)
        else:
            colour = RULE
        rect(slide, 0.30, ty, 0.14 if i == idx else 0.075, 0.013, fill=colour)
    # header
    block(
        slide,
        0.62,
        0.44,
        9.0,
        0.24,
        [{"text": f"{idx:02d} — {section}", "spc": 2.0, "bold": True}],
        size=9,
        color=ACCENT,
        caps=True,
    )
    block(slide, 0.62, 0.74, 11.4, 0.72, [{"text": title}], size=30, bold=True, line=0.98)
    if lede:
        block(slide, 0.62, 1.42, 9.6, 0.30, [{"text": lede}], size=11.5, color=MUTED, line=1.0)
    # footer
    rect(slide, 0.62, 6.92, 12.09, 0.010, fill=RULE)
    block(
        slide,
        0.62,
        7.02,
        6.0,
        0.20,
        [{"text": "PALM / SIGN  ·  MINOR PROJECT  ·  2026", "spc": 1.4}],
        size=7.5,
        color=MUTED,
        caps=True,
    )
    block(
        slide,
        11.9,
        7.02,
        0.82,
        0.20,
        [{"text": f"{idx:02d} / {TOTAL:02d}", "spc": 1.2}],
        size=7.5,
        color=MUTED,
        align=PP_ALIGN.RIGHT,
    )


def stat(slide, x, y, value, label, w=1.9, vsize=26, unit=None):
    runs = [(value, {"size": vsize, "font": LIGHT})]
    if unit:
        runs.append((unit, {"size": vsize * 0.55, "color": ACCENT}))
    block(slide, x, y, w, 0.46, [{"text": runs}], size=vsize, color=CREAM, line=0.95)
    block(
        slide,
        x,
        y + 0.44,
        w,
        0.5,
        [{"text": label}],
        size=8,
        color=MUTED,
        line=1.05,
        caps=True,
        spc=0.8,
    )


def rule(slide, x, y, w, color=RULE, h=0.010):
    rect(slide, x, y, w, h, fill=color)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def new(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# ------------------------------------------------------------------ 01 cover
def cover(prs):
    s = new(prs)
    rect(s, 0, 0, W, H, fill=BG)
    block(
        s,
        0.75,
        0.62,
        8.0,
        0.24,
        [{"text": "MINOR PROJECT  ·  COMPUTER VISION  ·  2026", "spc": 2.4, "bold": True}],
        size=9,
        color=MUTED,
    )
    block(
        s,
        0.70,
        0.98,
        7.6,
        1.10,
        [{"text": [("PALM", {}), (" / ", {"color": ACCENT}), ("SIGN", {})]}],
        size=64,
        font=LIGHT,
        color=TEXT,
        line=0.95,
        spc=-1.0,
    )
    block(
        s,
        0.75,
        2.16,
        6.4,
        0.90,
        [{"text": "A real-time vision workbench for fingerspelled hand signs"}],
        size=18,
        color=RGBColor(0xC9, 0xD5, 0xE4),
        line=1.15,
    )
    block(
        s,
        0.75,
        2.78,
        6.4,
        0.30,
        [
            {
                "text": "26 letters  ·  61-D shape descriptor  ·  97.7 % held-out accuracy",
                "spc": 0.4,
            }
        ],
        size=11,
        color=MUTED,
    )
    rect(s, 0.75, 3.30, 1.15, 0.035, fill=ACCENT)

    block(
        s,
        0.75,
        3.62,
        3.2,
        0.22,
        [{"text": "PRESENTED BY", "spc": 2.0, "bold": True}],
        size=8,
        color=MUTED,
    )
    block(s, 0.75, 3.86, 4.0, 0.30, [{"text": "Samarth Vegada"}], size=14, bold=True)
    block(
        s,
        0.75,
        4.16,
        4.0,
        0.26,
        [{"text": "Enrollment No. [Enrollment Number]"}],
        size=10,
        color=MUTED,
    )
    block(
        s,
        0.75,
        4.72,
        3.2,
        0.22,
        [{"text": "FACULTY GUIDE", "spc": 2.0, "bold": True}],
        size=8,
        color=MUTED,
    )
    block(
        s,
        0.75,
        4.96,
        4.4,
        0.28,
        [{"text": "[Name of Faculty Mentor]"}],
        size=12,
        color=RGBColor(0xC9, 0xD5, 0xE4),
    )
    rule(s, 0.75, 5.72, 5.6, RULE)
    block(
        s,
        0.75,
        5.90,
        5.6,
        0.52,
        [{"text": "Adani University  ·  B.Tech CSE (AI–ML)"}, {"text": "School of Computing  ·  November 2026"}],
        size=10,
        color=MUTED,
        line=1.35,
    )

    # camera viewfinder plate
    vx, vy, vw, vh = 7.35, 1.28, 5.22, 3.92
    plate(
        s,
        "fig_5_7_overlay.png",
        vx,
        vy,
        vw,
        vh,
        "Live overlay: face exclusion, region of interest, hull and defects",
        pad=0.14,
    )
    # corner brackets
    for cx, cy, dx, dy in (
        (vx - 0.10, vy - 0.10, 1, 1),
        (vx + vw + 0.10, vy - 0.10, -1, 1),
        (vx - 0.10, vy + vh + 0.10, 1, -1),
        (vx + vw + 0.10, vy + vh + 0.10, -1, -1),
    ):
        hx = cx if dx > 0 else cx - 0.34
        hy = cy if dy > 0 else cy - 0.035
        rect(s, hx, hy, 0.34, 0.035, fill=ACCENT)
        vxx = cx if dx > 0 else cx - 0.035
        vyy = cy if dy > 0 else cy - 0.34
        rect(s, vxx, vyy, 0.035, 0.34, fill=ACCENT)

    # chips
    chips = ["30 FPS CAPTURE", "61-D DESCRIPTOR", "SVC · RBF"]
    cx = vx
    for c in chips:
        wdt = 0.20 + len(c) * 0.082
        rect(s, cx, 5.62, wdt, 0.30, fill=None, line=RULE, lw=0.9, radius=0.35)
        block(
            s,
            cx,
            5.66,
            wdt,
            0.22,
            [{"text": c, "spc": 1.2, "align": PP_ALIGN.CENTER}],
            size=7.5,
            color=MUTED,
            bold=True,
        )
        cx += wdt + 0.14

    notes(
        s,
        "Open by naming the artefact: not a classifier in a notebook, but a workbench that "
        "captures, explains, trains and reports. The frame on the right is a real frame from "
        "the running application.",
    )


# ------------------------------------------------------------------ 02 agenda
def agenda(prs):
    s = new(prs)
    chrome(s, 1, "Contents", "Six things, in the order they happened")
    items = [
        ("01", "The gap", "Why a demo is not a workbench, and what is missing"),
        ("02", "The vocabulary", "Twenty-six letters, captured one frame at a time"),
        ("03", "The pipeline", "From pixels to a sixty-one dimensional descriptor"),
        ("04", "The model", "One RBF support-vector classifier, nothing exotic"),
        ("05", "The evidence", "1,747 held-out frames, reported per sign"),
        ("06", "The product", "A browser workbench that shows every stage"),
    ]
    col_x = (0.62, 6.95)
    for i, (num, title, sub) in enumerate(items):
        x = col_x[i // 3]
        y = 1.95 + (i % 3) * 1.52
        rule(s, x, y, 5.75, RULE)
        block(
            s,
            x,
            y + 0.18,
            0.7,
            0.28,
            [{"text": num, "spc": 1.6, "bold": True}],
            size=10,
            color=ACCENT,
        )
        block(s, x + 0.72, y + 0.12, 4.9, 0.34, [{"text": title}], size=17, bold=True)
        block(
            s, x + 0.72, y + 0.50, 4.9, 0.32, [{"text": sub}], size=10.5, color=MUTED, line=1.1
        )
    rule(s, 0.62, 6.62, 12.09, RULE)
    block(
        s,
        0.62,
        6.70,
        11.0,
        0.24,
        [{"text": "Every number in this deck comes from the saved model bundle, not from a slide."}],
        size=9,
        color=MUTED,
        italic=True,
    )
    notes(s, "Signpost only. Keep it to twenty seconds; the audience wants the demo.")


# ------------------------------------------------------------------ 03 problem
def problem(prs):
    s = new(prs)
    chrome(
        s,
        2,
        "The gap",
        "A notebook is not a workbench",
        "Recognition demos are easy to record and hard to trust.",
    )
    block(
        s,
        0.62,
        1.92,
        6.55,
        1.40,
        [
            {
                "text": "A single accuracy figure hides everything that matters. When the model "
                "returns the wrong letter, the mask, the contour and the descriptor are all "
                "invisible, so the failure cannot be explained or fixed."
            }
        ],
        size=13.5,
        color=RGBColor(0xD3, 0xDD, 0xEA),
        line=1.38,
    )
    rows = [
        ("No visibility", "Four segmentation stages run, and none of them can be inspected."),
        ("No repeatability", "Each experiment lives in its own notebook cell and its own path."),
        ("No loop", "Capture, train, evaluate and reset are four separate scripts."),
    ]
    for i, (head, body) in enumerate(rows):
        y = 3.36 + i * 0.98
        rule(s, 0.62, y, 6.55, RULE)
        block(s, 0.62, y + 0.14, 6.3, 0.26, [{"text": head}], size=11.5, bold=True, color=ACCENT_L)
        block(s, 0.62, y + 0.44, 6.3, 0.42, [{"text": body}], size=10.5, color=MUTED, line=1.15)

    # right panel
    rect(s, 7.55, 1.90, 5.16, 4.62, fill=PANEL, radius=0.03)
    block(
        s,
        7.92,
        2.16,
        4.4,
        0.24,
        [{"text": "WHAT THE USER ACTUALLY NEEDS", "spc": 1.8, "bold": True}],
        size=8,
        color=ACCENT,
    )
    wants = [
        "Capture a labelled frame and see the mask it produced",
        "Watch each stage of the pipeline, not just the answer",
        "Train from the same page that captured the data",
        "Read per-sign accuracy instead of one headline number",
        "Reset the dataset and start again without a terminal",
        "Keep the data, the model and the numbers in one place",
    ]
    for i, wtext in enumerate(wants):
        y = 2.58 + i * 0.62
        block(
            s,
            7.92,
            y,
            4.45,
            0.54,
            [{"text": wtext, "bullet": True}],
            size=10.5,
            color=RGBColor(0xD3, 0xDD, 0xEA),
            line=1.15,
        )
    notes(
        s,
        "The argument: the interesting engineering is not the classifier, it is making the "
        "classifier legible and repeatable.",
    )


# ------------------------------------------------------------------ 04 objectives
def objectives(prs):
    s = new(prs)
    chrome(
        s,
        3,
        "Objectives",
        "Four commitments, one honest scope",
        "What the project set out to deliver, in the order it was built.",
    )
    cards = [
        (
            "01",
            "Capture",
            "A browser-driven loop that stores the frame, the 180 × 180 mask and the label together, "
            "so no example is ever unlabelled.",
        ),
        (
            "02",
            "Explain",
            "Expose every stage: skin mask, largest component, contour, convex hull, defect points "
            "and the descriptor itself.",
        ),
        (
            "03",
            "Classify",
            "One 61-D shape descriptor and one RBF support-vector classifier, scored per sign rather "
            "than in aggregate.",
        ),
        (
            "04",
            "Operate",
            "A single Flask workbench — capture, train, evaluate, reset — with no notebook and no "
            "terminal in the loop.",
        ),
    ]
    for i, (num, head, body) in enumerate(cards):
        x = 0.62 + (i % 2) * 6.24
        y = 1.92 + (i // 2) * 2.06
        rect(s, x, y, 5.86, 1.58, fill=PANEL, radius=0.035)
        block(s, x + 0.34, y + 0.24, 0.6, 0.24, [{"text": num, "bold": True}], size=9.5, color=ACCENT)
        block(s, x + 0.34, y + 0.52, 5.1, 0.32, [{"text": head}], size=15, bold=True)
        block(
            s,
            x + 0.34,
            y + 0.86,
            5.15,
            0.62,
            [{"text": body}],
            size=10,
            color=MUTED,
            line=1.2,
        )

    rect(s, 0.62, 6.12, 12.09, 0.52, fill=None, line=RULE, lw=0.9, radius=0.06)
    block(
        s,
        0.92,
        6.24,
        11.6,
        0.30,
        [
            {
                "text": [
                    ("SCOPE  ", {"color": ACCENT, "bold": True, "spc": 1.4}),
                    (
                        "Static fingerspelling, A to Z, one hand, one camera. Continuous ISL and "
                        "two-handed signs are explicitly out of scope.",
                        {"color": MUTED},
                    ),
                ]
            }
        ],
        size=9.5,
    )
    notes(
        s,
        "Be explicit about the boundary. A minor project that claims continuous ISL and does not "
        "deliver it is weaker than one that scopes tightly and delivers completely.",
    )


# ------------------------------------------------------------------ 05 vocabulary
def vocabulary(prs):
    s = new(prs)
    chrome(
        s,
        4,
        "The vocabulary",
        "Twenty-six letters, captured by hand",
        "One stored mask per sign, taken from the dataset the model was trained on.",
    )
    plate(s, "fig_5_5_mask_gallery.png", 0.62, 1.86, 7.35, 4.72)
    stats = [
        ("26", "classes, A to Z"),
        ("6,983", "captured frames"),
        ("700", "masks kept on disk"),
        ("160–400", "frames per sign"),
    ]
    for i, (v, l) in enumerate(stats):
        stat(s, 8.35, 1.95 + i * 1.16, v, l, w=4.2, vsize=25)
    block(
        s,
        8.35,
        6.30,
        4.25,
        0.44,
        [{"text": "Weakest signs are the ones captured last."}],
        size=8.5,
        color=MUTED,
        italic=True,
        line=1.1,
    )
    notes(
        s,
        "Point at the imperfections: blurred fingertips, a sliver of sleeve. Those are the actual "
        "difficulty, and they are why the descriptor is shape-based rather than template-based.",
    )


# ------------------------------------------------------------------ 06 architecture
def architecture(prs):
    s = new(prs)
    chrome(
        s,
        5,
        "Architecture",
        "Three processes, one page",
        "The browser never touches OpenCV; the camera thread never touches the request.",
    )
    plate(
        s,
        "fig_5_1_architecture.png",
        0.62,
        1.92,
        6.95,
        4.62,
        "Component view of the workbench: capture thread, feature engine and Flask API",
    )
    items = [
        ("Capture thread", "30 fps grab, face exclusion, ROI crop; the mask is written next to the frame."),
        ("Feature engine", "Contour → hull → defects → 61-D vector, with no learned preprocessing."),
        ("Flask API", "/api/state, /api/capture and /api/train; the page polls, it never blocks."),
    ]
    for i, (head, body) in enumerate(items):
        y = 1.98 + i * 1.55
        rule(s, 7.95, y, 4.76, RULE)
        block(s, 7.95, y + 0.14, 4.7, 0.26, [{"text": head}], size=11.5, bold=True, color=ACCENT_L)
        block(s, 7.95, y + 0.44, 4.72, 0.90, [{"text": body}], size=9.5, color=MUTED, line=1.25)
    block(
        s,
        7.95,
        6.42,
        4.7,
        0.24,
        [{"text": "OpenCV · scikit-learn · Flask · vanilla JS", "spc": 0.8}],
        size=8,
        color=MUTED,
    )
    notes(
        s,
        "The separation is the point: a slow classifier can never stall the video, and a stalled "
        "browser can never drop a frame.",
    )


# ------------------------------------------------------------------ 07 pipeline
def pipeline(prs):
    s = new(prs)
    chrome(
        s,
        6,
        "Pipeline",
        "From a frame to a letter in ten steps",
        "Each stage is observable in the interface, and each stage can fail on its own.",
    )
    plate(
        s,
        "fig_5_2_pipeline.png",
        0.62,
        1.92,
        8.15,
        4.62,
        "The processing pipeline, from camera grab to committed letter",
    )
    stages = [
        ("Grab", "stages 1–2  ·  640 × 480 at 30 fps, mirror flip"),
        ("Skin mask", "stages 3–4  ·  HSV range, face removed"),
        ("Clean up", "stage 5  ·  morphology, largest component, ROI"),
        ("Normalise", "stage 6  ·  crop, pad, warp to 180 × 180"),
        ("Describe and decide", "stages 7–10  ·  61-D vector, SVC, 1.5 s hold"),
    ]
    for i, (head, sub) in enumerate(stages):
        y = 1.92 + i * 0.94
        block(s, 9.05, y - 0.02, 3.66, 0.26, [{"text": head}], size=10.5, bold=True)
        block(s, 9.05, y + 0.24, 3.66, 0.24, [{"text": sub}], size=8.5, color=MUTED)
        if i < 4:
            rule(s, 9.05, y + 0.60, 3.66, RGBColor(0x18, 0x28, 0x40))
    notes(
        s,
        "Walk the ten boxes once, quickly, grouping them into the five ideas on the right. The "
        "point to land is that the mask and the clean-up decide almost everything downstream.",
    )


# ------------------------------------------------------------------ 08 segmentation
def segmentation(prs):
    s = new(prs)
    chrome(
        s,
        7,
        "Segmentation",
        "The part that fails quietly",
        "If the mask is wrong, nothing downstream can be right.",
    )
    plate(
        s,
        "fig_5_6_segmentation_stages.png",
        0.62,
        1.86,
        8.55,
        2.45,
        "One stored mask through the geometric stages, ending in the radial signature",
    )
    plate(s, "fig_5_7_overlay.png", 9.35, 1.86, 3.34, 2.45, pad=0.10)
    rule(s, 0.62, 4.52, 12.09, RULE)
    notes_items = [
        ("Skin in HSV", "Hue and saturation separate skin from background under changing light."),
        ("Face removed", "A Haar cascade masks the face before the hand is measured."),
        ("One component", "Morphology, then only the largest blob is kept."),
        ("64 points", "The contour is resampled so the descriptor never depends on frame size."),
    ]
    for i, (head, body) in enumerate(notes_items):
        x = 0.62 + i * 3.10
        block(s, x, 4.72, 2.95, 0.24, [{"text": head}], size=10, bold=True, color=ACCENT_L)
        block(s, x, 5.00, 2.95, 1.00, [{"text": body}], size=9.2, color=MUTED, line=1.25)
    rule(s, 0.62, 5.98, 12.09, RULE)
    block(
        s,
        0.62,
        6.12,
        12.09,
        0.36,
        [
            {
                "text": "A mask that keeps a sleeve teaches the classifier that sleeves belong "
                "to the letter."
            }
        ],
        size=11,
        color=ACCENT_L,
        italic=True,
    )
    notes(
        s,
        "This is the slide that earns credibility: show a real mask and a real overlay, not a "
        "diagram of a hand.",
    )


# ------------------------------------------------------------------ 09 descriptor
def descriptor(prs):
    s = new(prs)
    chrome(
        s,
        8,
        "Features",
        "Sixty-one numbers, four blocks",
        "Fixed length, normalised, and cheap enough to compute on every frame.",
    )
    # native segmented bar: 61 values, four blocks
    segs = [
        (10, "Geometry", ACCENT),
        (7, "Hu", RGBColor(0xF0, 0x8A, 0x6A)),
        (20, "Fourier", RGBColor(0x7D, 0x8C, 0xA3)),
        (24, "Radial", RGBColor(0x2C, 0x40, 0x5C)),
    ]
    bar_w = 6.60
    bx = 0.62
    for count, name, colour in segs:
        seg_w = bar_w * count / 61
        rect(s, bx, 2.12, seg_w, 0.46, fill=colour)
        block(
            s,
            bx,
            2.22,
            seg_w,
            0.24,
            [{"text": f"{name}  {count}", "align": PP_ALIGN.CENTER}],
            size=8.5,
            bold=True,
        )
        bx += seg_w
    block(
        s,
        0.62,
        2.68,
        6.60,
        0.24,
        [{"text": "61 values  ·  computed on every frame  ·  no learned preprocessing", "spc": 0.6}],
        size=8.5,
        color=MUTED,
    )

    rows = [
        ("Geometry", "10", "Solidity, extent, elongation, circularity, defect depth and count"),
        ("Hu moments", "7", "Log-scaled invariants h1 to h7; rotation invariant"),
        ("Fourier", "20", "Magnitudes of the first twenty contour coefficients"),
        ("Radial", "24", "Mean normalised radius in twenty-four angular bins"),
    ]
    for i, (name, n, desc) in enumerate(rows):
        y = 3.34 + i * 0.80
        rule(s, 0.62, y, 6.60, RULE)
        block(s, 0.62, y + 0.14, 1.95, 0.26, [{"text": name}], size=10.5, bold=True)
        block(s, 2.62, y + 0.14, 0.60, 0.26, [{"text": n}], size=10.5, bold=True, color=ACCENT)
        block(s, 3.28, y + 0.15, 3.95, 0.56, [{"text": desc}], size=8.8, color=MUTED, line=1.2)
    rule(s, 0.62, 3.34 + 4 * 0.80, 6.60, RULE)

    plate(
        s,
        "fig_5_4_geometry.png",
        7.75,
        1.86,
        4.96,
        4.24,
        "Hull, defects, centroid and the twenty-four radial bins",
        pad=0.14,
    )
    block(
        s,
        7.75,
        6.24,
        4.96,
        0.60,
        [
            {
                "text": "Scale and translation are normalised away, so distance from the camera "
                "stops mattering."
            }
        ],
        size=9,
        color=MUTED,
        line=1.25,
    )
    notes(
        s,
        "Emphasise that this is deliberately not a learned embedding. Every one of the sixty-one "
        "numbers can be pointed at on a picture, which is what makes errors explainable.",
    )


# ------------------------------------------------------------------ 10 dataset
def dataset(prs):
    s = new(prs)
    chrome(
        s,
        9,
        "Dataset",
        "Six thousand frames, honestly imbalanced",
        "Captured by one person, in one room, over several sessions.",
    )
    plate(
        s,
        "fig_6_19_class_distribution.png",
        0.62,
        1.88,
        5.55,
        4.66,
        "Graph 6.1 — captured frames per sign",
        pad=0.14,
    )
    stats = [
        ("6,983", "frames in total"),
        ("160", "frames for the smallest class (C, D)"),
        ("400", "frames for the largest class (O)"),
        ("1,747", "frames held out for testing"),
    ]
    for i, (v, l) in enumerate(stats):
        stat(s, 6.62, 1.92 + i * 1.10, v, l, w=3.2, vsize=24)
    rect(s, 10.05, 1.90, 2.66, 2.34, fill=PANEL, radius=0.04)
    block(
        s,
        10.30,
        2.14,
        2.2,
        0.60,
        [{"text": "The graph predicted the error table."}],
        size=11,
        bold=True,
        color=ACCENT_L,
        line=1.15,
    )
    block(
        s,
        10.30,
        2.86,
        2.2,
        1.20,
        [
            {
                "text": "B, C and D were captured last and have the fewest frames. They are also "
                "the three weakest signs in the held-out results."
            }
        ],
        size=9,
        color=MUTED,
        line=1.3,
    )
    notes(
        s,
        "Say the honest thing: the dataset is small and single-operator. The imbalance is not a "
        "surprise in the results, it is visible in the collection.",
    )


# ------------------------------------------------------------------ 11 model
def model(prs):
    s = new(prs)
    chrome(
        s,
        10,
        "Model",
        "One classifier, deliberately boring",
        "If a shape descriptor already reaches 97.7 %, the interesting work is elsewhere.",
    )
    rows = [
        ("Kernel", "RBF"),
        ("Regularisation, C", "8.0"),
        ("Gamma", "scale"),
        ("Input features", "61"),
        ("Classes", "26"),
        ("Split", "75 / 25, stratified"),
        ("Held-out frames", "1,747"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 1.92 + i * 0.62
        rule(s, 0.62, y, 5.55, RULE)
        block(s, 0.62, y + 0.13, 3.2, 0.26, [{"text": k}], size=10, color=MUTED)
        block(s, 3.85, y + 0.11, 2.3, 0.28, [{"text": v}], size=11.5, bold=True, align=PP_ALIGN.RIGHT)
    rule(s, 0.62, 1.92 + 7 * 0.62, 5.55, RULE)

    block(
        s,
        0.62,
        6.42,
        5.55,
        0.42,
        [{"text": "No CNN. No augmentation. No hyper-parameter search."}],
        size=9.5,
        color=ACCENT_L,
        italic=True,
    )

    plate(
        s,
        "fig_6_22_train_test.png",
        6.55,
        1.92,
        6.16,
        2.72,
        "Training fit against held-out accuracy, and the distribution of per-sign F1",
        pad=0.14,
    )
    block(
        s,
        6.55,
        4.86,
        6.16,
        1.55,
        [
            {
                "text": "The gap between 99.9 % on the training set and 97.7 % on held-out frames "
                "is 2.3 points. That is small enough to trust the number and large enough to know "
                "the model is not simply memorising the captures."
            }
        ],
        size=11,
        color=RGBColor(0xD3, 0xDD, 0xEA),
        line=1.35,
    )
    notes(
        s,
        "Defend the simplicity. A small, inspectable model with a measured error is worth more "
        "than a large model nobody can explain.",
    )


# ------------------------------------------------------------------ 12 results
def results(prs):
    s = new(prs)
    chrome(
        s,
        11,
        "Results",
        "97.7 % on frames the model never saw",
        "1,747 held-out frames across twenty-six classes.",
    )
    block(
        s,
        0.62,
        1.80,
        6.0,
        1.05,
        [{"text": [("97.7", {"font": LIGHT, "size": 82}), (" %", {"size": 30, "color": ACCENT})]}],
        line=0.9,
        color=CREAM,
    )
    block(
        s,
        0.62,
        2.92,
        5.6,
        0.26,
        [{"text": "held-out accuracy", "spc": 1.6}],
        size=9,
        color=MUTED,
        caps=True,
        bold=True,
    )
    stats = [
        ("97.5", "macro F1"),
        ("97.7", "weighted F1"),
        ("99.9", "training fit"),
        ("40", "errors in total"),
    ]
    for i, (v, l) in enumerate(stats):
        x = 0.62 + (i % 2) * 3.0
        y = 3.42 + (i // 2) * 1.12
        block(s, x, y, 2.8, 0.44, [{"text": v, "font": LIGHT}], size=26, color=CREAM)
        block(s, x, y + 0.44, 2.8, 0.24, [{"text": l}], size=8, color=MUTED, caps=True, spc=0.8)

    rule(s, 0.62, 5.92, 5.85, RULE)
    block(
        s,
        0.62,
        6.04,
        5.85,
        0.70,
        [
            {
                "text": "The heaviest confusions — B→K, A→L, V→W, Q→L — are all pairs that differ "
                "by a single finger."
            }
        ],
        size=9.5,
        color=MUTED,
        line=1.25,
    )
    plate(
        s,
        "fig_6_21_confusion_matrix.png",
        6.85,
        1.82,
        5.86,
        4.85,
        "Confusion matrix over the held-out split; the diagonal is the model agreeing with itself",
        pad=0.12,
    )
    notes(
        s,
        "Lead with the number, then immediately explain the 40 errors. An examiner will ask about "
        "them, and the confusion matrix already answers.",
    )


# ------------------------------------------------------------------ 13 per sign
def per_sign(prs):
    s = new(prs)
    chrome(
        s,
        12,
        "Per-sign results",
        "Accuracy is not one number",
        "Every sign carries its own recall, and the weakest signs are the least-captured ones.",
    )
    plate(
        s,
        "fig_6_20_per_sign_recall.png",
        0.62,
        1.88,
        5.30,
        4.72,
        "Graph 6.2 — held-out recall for each of the twenty-six signs",
        pad=0.14,
    )
    rows = [
        ("X, Y", "100 %", "Perfect recall on both signs", GREEN),
        ("U, W", "100 %", "No held-out frame missed", GREEN),
        ("A", "93.7 %", "Most often read as L", ACCENT),
        ("C", "92.5 %", "Captured last, only 160 frames", ACCENT),
        ("B", "91.7 %", "Weakest sign; confused with K", ACCENT),
    ]
    for i, (sign, val, note, col) in enumerate(rows):
        y = 1.92 + i * 0.94
        rule(s, 6.30, y, 6.40, RULE)
        block(s, 6.30, y + 0.14, 1.1, 0.26, [{"text": sign}], size=12, bold=True)
        block(s, 7.45, y + 0.13, 1.3, 0.26, [{"text": val}], size=12, bold=True, color=col)
        block(s, 8.95, y + 0.16, 3.75, 0.26, [{"text": note}], size=9, color=MUTED)
    rule(s, 6.30, 6.24, 6.40, RULE)
    block(
        s,
        6.30,
        6.36,
        6.40,
        0.30,
        [{"text": "The class the model sees least is the class it misses most."}],
        size=9.5,
        color=ACCENT_L,
        italic=True,
    )
    notes(
        s,
        "This slide exists because a single accuracy number would let a weak sign hide. The "
        "library in the product shows exactly these values.",
    )


# ------------------------------------------------------------------ 14 workbench
def workbench(prs):
    s = new(prs)
    chrome(
        s,
        13,
        "The product",
        "A browser, not a notebook",
        "One page, four working areas, no terminal.",
    )
    plate(
        s,
        "fig_6_16_lab.png",
        0.62,
        1.86,
        3.95,
        3.62,
        "The lab: skin range, four stage panels, capture controls",
        pad=0.12,
    )
    cards = [
        ("01", "Live desk", "Camera, current letter, confidence and a running transcript."),
        ("02", "Reading pane", "The recognised sentence, editable, with the held letter marked."),
        ("03", "Capture lab", "Frame, mask and label stored together; class counts update live."),
        ("04", "Train and reset", "Training runs in place and returns a fresh metrics bundle."),
    ]
    for i, (num, head, body) in enumerate(cards):
        x = 4.85 + (i % 2) * 4.00
        y = 1.86 + (i // 2) * 2.00
        rect(s, x, y, 3.85, 1.72, fill=PANEL, radius=0.04)
        block(s, x + 0.28, y + 0.22, 0.6, 0.22, [{"text": num, "bold": True}], size=8.5, color=ACCENT)
        block(s, x + 0.28, y + 0.50, 3.3, 0.28, [{"text": head}], size=13, bold=True)
        block(s, x + 0.28, y + 0.82, 3.30, 0.74, [{"text": body}], size=9.5, color=MUTED, line=1.25)

    rect(s, 0.62, 5.66, 3.95, 0.34, fill=None, line=RULE, lw=0.9, radius=0.3)
    block(
        s,
        0.62,
        5.72,
        3.95,
        0.22,
        [{"text": "127.0.0.1:5000  ·  Flask  ·  no build step", "spc": 0.6, "align": PP_ALIGN.CENTER}],
        size=7.5,
        color=MUTED,
    )
    notes(
        s,
        "This is the demo slide. If a live demo is possible, cut here and switch to the app; "
        "otherwise walk the four areas on the screenshot.",
    )


# ------------------------------------------------------------------ 15 library
def library(prs):
    s = new(prs)
    chrome(
        s,
        14,
        "Proof in the interface",
        "The numbers live where the work happens",
        "Nothing in this deck is a number the product cannot show you.",
    )
    plate(
        s,
        "fig_6_17_library.png",
        0.62,
        1.86,
        5.30,
        4.70,
        "Sign library: frame count and held-out accuracy for every letter",
        pad=0.14,
    )
    plate(
        s,
        "fig_6_18_training.png",
        6.20,
        1.86,
        6.50,
        2.62,
        "Training returns accuracy, split size and per-sign metrics",
        pad=0.10,
    )
    block(
        s,
        6.20,
        4.66,
        6.50,
        1.00,
        [
            {
                "text": "Every tile reports how many frames were captured for that sign and how "
                "well the model recognises it, so a weak sign is visible before anyone opens a "
                "report."
            }
        ],
        size=10.5,
        color=RGBColor(0xD3, 0xDD, 0xEA),
        line=1.32,
    )
    facts = [
        ("6,983", "frames counted by the page"),
        ("97.7 %", "reported after training"),
        ("26", "per-sign rows, not an average"),
    ]
    for i, (v, l) in enumerate(facts):
        x = 6.20 + i * 2.20
        block(s, x, 5.82, 2.05, 0.34, [{"text": v, "font": LIGHT}], size=18, color=CREAM)
        block(s, x, 6.20, 2.05, 0.40, [{"text": l}], size=8, color=MUTED, line=1.1)
    notes(
        s,
        "The strongest argument for the workbench: the evaluation is part of the product, not a "
        "separate document.",
    )


# ------------------------------------------------------------------ 16 engineering
def engineering(prs):
    s = new(prs)
    chrome(
        s,
        15,
        "Engineering",
        "Built in increments, not in one go",
        "Four increments, each ending in something demonstrable in the browser.",
    )
    plate(
        s,
        "fig_6_3_activity.png",
        0.62,
        1.88,
        3.95,
        4.80,
        "Activity model of one recognition cycle",
        pad=0.14,
    )
    incs = [
        ("01", "Capture only", "A page that grabs frames and writes labelled masks to disk."),
        ("02", "Features and a first classifier", "61-D descriptor, SVC, accuracy on a fixed split."),
        ("03", "Live overlay", "Hull, defects and the hold timer drawn on the streamed frame."),
        ("04", "Workbench", "Per-sign reporting, reset, and the library inside the product."),
    ]
    for i, (num, head, body) in enumerate(incs):
        y = 1.90 + i * 1.20
        rule(s, 4.95, y, 7.75, RULE)
        block(s, 4.95, y + 0.14, 0.5, 0.24, [{"text": num, "bold": True}], size=8.5, color=ACCENT)
        block(s, 5.45, y + 0.11, 7.1, 0.26, [{"text": head}], size=11, bold=True)
        block(s, 5.45, y + 0.42, 7.1, 0.42, [{"text": body}], size=9, color=MUTED, line=1.2)
    rule(s, 4.95, 1.90 + 4 * 1.20, 7.75, RULE)

    rect(s, 4.95, 6.42, 7.75, 0.36, fill=None, line=RULE, lw=0.9, radius=0.2)
    block(
        s,
        5.15,
        6.48,
        7.4,
        0.24,
        [{"text": "12 UML diagrams  ·  four iterations  ·  one refactor of the engine", "spc": 0.6}],
        size=8,
        color=MUTED,
    )
    notes(
        s,
        "Mention the refactor honestly: capture and live recognition were separate engines until "
        "increment three, and merging them removed a class of duplicated bugs.",
    )


# ------------------------------------------------------------------ 17 lessons
def lessons(prs):
    s = new(prs)
    chrome(
        s,
        16,
        "What broke",
        "Four failures worth keeping",
        "Every one of these was found by looking at the overlay, not at the accuracy.",
    )
    items = [
        (
            "A sleeve became part of the hand",
            "Crop to the region of interest, then keep only the largest connected component.",
        ),
        (
            "Fingertips blurred at the edge of the mask",
            "Normalise to 180 × 180 and describe direction with radial bins, not point matching.",
        ),
        (
            "The headline accuracy hid three weak signs",
            "Stratified split, then per-sign precision, recall and F1 in both the report and the UI.",
        ),
        (
            "The page stuttered while the model trained",
            "Decouple the 30 fps capture thread from the request cycle; the page polls state.",
        ),
    ]
    block(
        s,
        1.30,
        1.80,
        4.0,
        0.22,
        [{"text": "WHAT FAILED", "spc": 1.8, "bold": True}],
        size=8,
        color=ACCENT,
    )
    block(
        s,
        6.60,
        1.80,
        4.0,
        0.22,
        [{"text": "WHAT FIXED IT", "spc": 1.8, "bold": True}],
        size=8,
        color=ACCENT,
    )
    for i, (head, fix) in enumerate(items):
        y = 2.12 + i * 1.06
        rule(s, 0.62, y, 12.09, RULE)
        block(s, 0.62, y + 0.16, 0.55, 0.30, [{"text": f"{i + 1:02d}"}], size=9, bold=True, color=ACCENT)
        block(s, 1.30, y + 0.12, 4.95, 0.34, [{"text": head}], size=12, bold=True, line=1.1)
        block(s, 6.60, y + 0.14, 6.10, 0.62, [{"text": fix}], size=9.8, color=MUTED, line=1.25)
    rule(s, 0.62, 2.12 + 4 * 1.06, 12.09, RULE)
    block(
        s,
        0.62,
        6.46,
        12.0,
        0.30,
        [{"text": "None of these appeared in the accuracy curve. All of them appeared in the frame."}],
        size=9.5,
        color=ACCENT_L,
        italic=True,
    )
    notes(
        s,
        "Judges reward this slide. It shows the project was debugged against reality rather than "
        "against a metric.",
    )


# ------------------------------------------------------------------ 18 conclusion
def conclusion(prs):
    s = new(prs)
    chrome(
        s,
        17,
        "Conclusion",
        "Done, and honest about it",
        "A small model made legible, end to end.",
    )
    takeaways = [
        "A 61-D shape descriptor with an RBF SVC reaches 97.7 % on held-out frames across 26 signs.",
        "Every stage of the pipeline is visible, so a wrong letter can be traced to a wrong mask.",
        "Evaluation lives in the product: per-sign accuracy, frame counts and a fresh metrics bundle.",
        "The workbench removes the notebook from the loop without hiding anything behind it.",
        "The report, the deck and the product all quote the same saved numbers.",
    ]
    block(
        s,
        0.62,
        1.90,
        6.30,
        0.24,
        [{"text": "WHAT THE PROJECT SHOWED", "spc": 1.8, "bold": True}],
        size=8,
        color=ACCENT,
    )
    for i, t in enumerate(takeaways):
        y = 2.26 + i * 0.86
        block(
            s,
            0.62,
            y,
            6.25,
            0.74,
            [{"text": t, "bullet": True}],
            size=11.2,
            color=RGBColor(0xD3, 0xDD, 0xEA),
            line=1.22,
        )

    rect(s, 7.25, 1.86, 5.46, 4.66, fill=PANEL, radius=0.035)
    block(
        s,
        7.60,
        2.12,
        4.8,
        0.24,
        [{"text": "WHAT COMES NEXT", "spc": 1.8, "bold": True}],
        size=8,
        color=ACCENT,
    )
    futures = [
        "Continuous ISL, where letters run together",
        "Two-handed and moving signs",
        "Calibration for a second operator and a new camera",
        "On-device inference to remove the server",
        "A public capture set other students can train on",
    ]
    for i, t in enumerate(futures):
        y = 2.56 + i * 0.90
        block(
            s,
            7.60,
            y,
            4.75,
            0.74,
            [{"text": t, "bullet": True, "bullet_color": GREEN}],
            size=11.2,
            color=RGBColor(0xD3, 0xDD, 0xEA),
            line=1.2,
        )
    notes(
        s,
        "Close on the engineering claim, not the accuracy claim: the contribution is legibility "
        "and repeatability, and the accuracy is the evidence that it works.",
    )


# ------------------------------------------------------------------ 19 closing
def closing(prs):
    s = new(prs)
    rect(s, 0, 0, W, H, fill=BG)
    rect(s, 0, 0, 0.16, H, fill=ACCENT)
    block(
        s,
        0.95,
        0.68,
        7.0,
        0.24,
        [{"text": "PALM / SIGN  ·  MINOR PROJECT", "spc": 2.2, "bold": True}],
        size=9,
        color=MUTED,
    )
    block(s, 0.90, 1.95, 11.0, 1.20, [{"text": "Thank you"}], size=60, font=LIGHT, line=0.95)
    rect(s, 0.95, 3.30, 1.15, 0.035, fill=ACCENT)
    block(
        s,
        0.95,
        3.62,
        7.0,
        0.40,
        [{"text": "Questions, and then the workbench is running."}],
        size=15,
        color=RGBColor(0xC9, 0xD5, 0xE4),
    )
    block(
        s,
        0.95,
        4.55,
        6.4,
        0.90,
        [
            {"text": "Samarth Vegada", "size": 12, "bold": True},
            {"text": "B.Tech CSE (AI–ML)  ·  Adani University", "size": 10, "color": MUTED},
            {"text": "November 2026", "size": 10, "color": MUTED},
        ],
        line=1.35,
    )
    # quiet motif: the size of the vocabulary, set as a ghost numeral
    block(
        s,
        8.55,
        1.55,
        4.15,
        2.35,
        [{"text": "26", "font": LIGHT, "align": PP_ALIGN.RIGHT}],
        size=170,
        color=RGBColor(0x15, 0x27, 0x3E),
        line=0.9,
    )
    block(
        s,
        8.55,
        3.95,
        4.15,
        0.26,
        [{"text": "letters, one workbench", "align": PP_ALIGN.RIGHT, "spc": 2.0}],
        size=8.5,
        color=MUTED,
        caps=True,
    )
    notes(s, "Stop talking. Let the demo answer the rest.")


# ------------------------------------------------------------------ build
def build() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    for fn in (
        cover,
        agenda,
        problem,
        objectives,
        vocabulary,
        architecture,
        pipeline,
        segmentation,
        descriptor,
        dataset,
        model,
        results,
        per_sign,
        workbench,
        library,
        engineering,
        lessons,
        conclusion,
        closing,
    ):
        fn(prs)
    prs.core_properties.title = "PALM / SIGN — A Real-Time Vision Workbench for Fingerspelled Hand Signs"
    prs.core_properties.author = "Samarth Vegada"
    prs.core_properties.subject = "Minor project presentation, Adani University, 2026"
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print("wrote", path, path.stat().st_size, "bytes")
