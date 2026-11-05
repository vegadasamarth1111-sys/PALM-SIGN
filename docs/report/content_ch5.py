"""Chapter 5: Technical Part."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Cm, Pt

import report_data as D
from report_lib import bullets, chapter, figure, h2, h3, para, table, table_caption


def equation(doc, parts, number: str) -> None:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Cm(7.1), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Cm(14.4), WD_TAB_ALIGNMENT.RIGHT)
    pf.space_before = Pt(8)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.5
    p.add_run("\t")
    for text, opts in parts:
        run = p.add_run(text)
        run.italic = opts.get("italic", True)
        if opts.get("sub"):
            run.font.subscript = True
        if opts.get("sup"):
            run.font.superscript = True
        run.font.name = "Times New Roman"
    p.add_run(f"\t({number})")


UPRIGHT = {"italic": False}


def chapter5(doc) -> None:
    chapter(doc, 5, "Technical Part")

    para(
        doc,
        "This chapter describes the technical core of the workbench: what the system assumes about "
        "hand shapes, where it can be applied, and how a frame of video becomes a letter. The "
        "treatment is detailed because the design decisions are the contribution; the classifier "
        "itself is a standard support vector machine.",
    )

    h2(doc, "5.1", "Concept")
    para(
        doc,
        "The central idea is that a fingerspelled letter is a shape, not a texture. Two photographs "
        "of the same letter taken at different distances, in different rooms, by different people "
        "differ enormously at the pixel level but share a silhouette: the number of extended "
        "fingers, the angles between them, the depth of the valleys between adjacent fingers, and "
        "the overall outline of the palm. If those geometric properties can be measured in a way "
        "that is invariant to position, scale and small rotations, a classifier trained on a few "
        "hundred examples per letter can generalise far beyond the pixels it has seen.",
    )
    para(
        doc,
        "The system therefore performs a deliberate compression. A 640 \u00d7 480 frame contains "
        "921,600 pixel values; the descriptor that reaches the classifier contains sixty-one "
        "numbers. The compression is lossy, and Chapter 7 discusses what is lost, but it is what "
        "makes a small dataset sufficient and a CPU fast enough.",
    )
    para(
        doc,
        "A second idea concerns time. A single frame is a weak observation: fingers move, the "
        "segmentation flickers and a letter that looks like B for three frames may look like D for "
        "one. The workbench therefore separates recognition from commitment. Recognition produces a "
        "label and a probability every frame; commitment requires the same label to dominate a "
        "nine-frame window and to hold for 1.5 seconds. The user sees a live reading and a separate, "
        "deliberate transcript, which mirrors how a human reader waits for a sign to settle.",
    )
    figure(doc, D.fig("5.1"), "5.1",
           "Layered architecture of the workbench, from the browser down to the camera", width_cm=13.4)
    para(
        doc,
        "Figure 5.1 shows the five layers that make up the application. The presentation layer never "
        "touches OpenCV, and the vision layer never touches HTTP; the engine in the middle owns the "
        "shared state and the lock that protects it. This separation is what allows the browser to "
        "poll a JSON snapshot twice a second while the camera thread runs at thirty frames per "
        "second.",
    )

    h2(doc, "5.2", "Application Area")
    para(
        doc,
        "The workbench is a general shape-recognition pipeline with a fingerspelling front end, and "
        "the application areas follow from that combination."
    )
    bullets(
        doc,
        [
            ("Accessibility. ", "A deaf or hard-of-hearing user can fingerspell a name or a short "
             "instruction and have it appear as editable text that the browser can speak aloud."),
            ("Classroom practice. ", "A learner can see per-sign accuracy and the confusion matrix, "
             "which turns practice into a measurable exercise rather than a guessing game."),
            ("Human\u2013computer interaction research. ", "The stage inspector makes the pipeline a "
             "testbed for segmentation thresholds, descriptors and temporal filters."),
            ("Low-resource deployment. ", "Because inference is local and cheap, the same design can "
             "run on a kiosk, a Raspberry Pi with a camera, or an offline laptop in a rural clinic."),
            ("Teaching computer vision. ", "Every classical technique in the pipeline, from CLAHE to "
             "convexity defects, is visible in the interface and can be demonstrated live."),
        ],
    )
    para(
        doc,
        "The system is not a substitute for a human interpreter in high-stakes settings such as "
        "medical or legal conversations. Its realistic role is the low-stakes, high-frequency "
        "exchange for which no interpreter would ever be booked.",
    )

    h2(doc, "5.3", "Acquisition and Pre-processing")
    para(
        doc,
        "Frames are read from the camera at 640 \u00d7 480 and mirrored horizontally so that the "
        "image behaves like a mirror and moving the hand right moves the silhouette right. The "
        "frame is converted from BGR to the LAB colour space, and contrast-limited adaptive "
        "histogram equalisation is applied to the L channel with a clip limit of 2.0 and an 8 \u00d7 "
        "8 tile grid. Unlike global equalisation, CLAHE does not amplify noise in flat regions, "
        "which matters because the background is usually a plain wall.",
    )
    para(
        doc,
        "A region of interest is then applied. The normalised box starts at 47 per cent of the frame "
        "width and spans the right half of the image, from four per cent to ninety-eight per cent of "
        "the height. The choice is pragmatic: the user sits slightly left of centre, so the hand is "
        "naturally held in the right half, and restricting the search removes most of the wall and "
        "all of the furniture from consideration. Everything outside the box is drawn dimmed in the "
        "live view, which teaches the user where to hold the hand without a written instruction.",
    )
    figure(doc, D.fig("5.2"), "5.2",
           "The ten-stage recognition pipeline, from frame acquisition to a committed letter",
           width_cm=14.2)
    para(
        doc,
        "Figure 5.2 is the pipeline that runs for every frame. The top row is image formation and "
        "segmentation, the bottom row is description and decision. The wrap from stage five to stage "
        "six is where the contour leaves image coordinates and enters shape coordinates.",
    )

    h2(doc, "5.4", "Hand Segmentation")
    para(
        doc,
        "Segmentation converts a colour image into a binary hand mask. The corrected frame is "
        "converted to HSV, and a broad in-range test is applied. Three presets are provided because "
        "no single range survives both a bright window and a dim corner; Table 5.1 lists the bounds. "
        "The default is the room-light preset, which was used for the reported dataset.",
    )
    table_caption(doc, "5.1", "HSV skin ranges exposed as presets in the laboratory panel")
    table(
        doc,
        ["Preset", "Lower bound (H, S, V)", "Upper bound (H, S, V)", "Typical use"],
        [
            ("Daylight", "(0, 28, 48)", "(22, 175, 255)", "Near a window, bright diffuse light"),
            ("Room light", "(0, 26, 34)", "(26, 195, 255)", "Default; desk lamp in the evening"),
            ("Low light", "(0, 36, 22)", "(29, 220, 240)", "Dim room, camera gain raised"),
        ],
        widths=[3.2, 4.2, 4.2, 3.0],
        align="center",
        first_col_bold=True,
    )
    para(
        doc,
        "The raw mask is noisy. A morphological close with an elliptical kernel reconnects fingers "
        "that the threshold has broken, and an open removes isolated speckles on the wall. The face "
        "is then detected on the original frame with a Haar cascade and the detected rectangle, "
        "expanded by a small margin, is cleared from the mask. This step is the difference between a "
        "system that works when the user looks at the screen and one that only works in profile.",
    )
    para(
        doc,
        "Contours are extracted from the cleaned mask and the largest contour whose area exceeds a "
        "minimum is kept. Its convex hull and convexity defects are computed, and a hand is declared "
        "present only if the contour is large enough and sufficiently solid. The result is a "
        "contour, a hull, a set of defect points and a normalised 180 \u00d7 180 mask that is stored "
        "with every captured frame.",
    )
    figure(doc, D.fig("5.3"), "5.3",
           "One stored 180 \u00d7 180 skin mask for each of the twenty-six signs, taken from the "
           "captured dataset", width_cm=14.2)
    para(
        doc,
        "Figure 5.3 is not an idealised illustration; it is the actual stored mask for one frame of "
        "each sign. The variation is instructive. Some masks are clean silhouettes, others are "
        "blurred at the fingertips or carry a fragment of a sleeve. Those imperfections are exactly "
        "what the classifier has to tolerate, and they explain why a purely geometric descriptor "
        "outperforms a brittle template match.",
    )
    figure(doc, D.fig("5.4"), "5.4",
           "Processing a stored mask for the letter P: raw mask, largest component after morphology, "
           "contour with convex hull and defects, and the radial signature", width_cm=14.4)
    para(
        doc,
        "Figure 5.4 follows one mask through the geometric stages. The hull in panel (c) is the "
        "smallest convex shape that contains the hand, and the marked points are the deep valleys "
        "between the thumb and the index finger and between the fingers. Panel (d) shows the "
        "centroid and the twenty-four rays used by the radial signature described in the next "
        "section.",
    )
    figure(doc, D.fig("5.5"), "5.5",
           "Live overlay from the running application: face exclusion box, region-of-interest "
           "brackets, hand hull and defect markers", width_cm=12.4)
    para(
        doc,
        "Figure 5.5 is a frame saved from the running application. The box around the face is the "
        "cascade detection that removes the face from the skin mask; the orange outline is the hand "
        "hull; the small dots are convexity defects. The overlay is drawn on the same frame that is "
        "streamed to the browser, so what the reader sees here is what the user sees.",
    )

    h2(doc, "5.5", "Feature Extraction")
    para(
        doc,
        "The descriptor is a fixed-length vector of sixty-one values in four blocks. Every block is "
        "normalised so that the same sign is described similarly whether the hand is close to the "
        "camera or far from it.",
    )
    figure(doc, D.fig("5.6"), "5.6",
           "Composition of the sixty-one dimensional feature vector", width_cm=14.0)
    table_caption(doc, "5.2", "Composition of the sixty-one dimensional feature vector")
    table(
        doc,
        ["Block", "Count", "Features", "Invariance"],
        [
            ("Geometry", "10", "Solidity, extent, elongation, circularity, finger estimate, defect "
             "count, maximum and mean defect depth, minimum defect angle, hull vertex count",
             "Scale and translation"),
            ("Hu moments", "7", "Log-scaled Hu moment invariants h1 to h7", "Scale, translation, rotation"),
            ("Fourier", "20", "Magnitudes of the first twenty FFT coefficients of the resampled "
             "complex contour, normalised by the first coefficient", "Scale, translation, starting point"),
            ("Radial", "24", "Mean normalised radius in twenty-four angular bins around the centroid",
             "Scale, translation"),
        ],
        widths=[2.6, 1.4, 7.6, 3.0],
        align="left",
        font_size=8.5,
        first_col_bold=True,
    )
    figure(doc, D.fig("5.7"), "5.7",
           "Geometric measurements used by the descriptor: convex hull, convexity defects, "
           "centroid, the twenty-four radial rays and the bounding box", width_cm=12.4)
    para(
        doc,
        "Figure 5.7 names the measurements that the first block of the descriptor records. The "
        "solid black line is the hand contour, the dashed red line is its convex hull, and the "
        "shaded circles mark the deepest convexity defects. Everything the classifier is told about "
        "the shape is derived from these few entities, which is why a misclassification can always "
        "be traced back to a specific measurement.",
    )
    para(
        doc,
        "The first block is direct geometry. Solidity is the ratio of contour area to hull area and "
        "falls when the fingers are spread; extent is the ratio of contour area to bounding-box area "
        "and rises for a closed fist; circularity captures how far the outline departs from a "
        "circle. Equation (5.1) gives solidity.",
    )
    equation(
        doc,
        [("S = ", {}), ("A", {}), ("contour", {"sub": True}), (" / ", {}), ("A", {}),
         ("hull", {"sub": True})],
        "5.1",
    )
    para(
        doc,
        "Convexity defects are the valleys between extended fingers. For each defect the system "
        "records the perpendicular depth and the angle at the far point, keeps at most the seven "
        "deepest valleys, and discards shallow ones that are caused by contour noise. The number of "
        "kept defects plus one is a first estimate of the extended finger count, capped at five.",
    )
    para(
        doc,
        "Hu moments are seven combinations of central moments that are invariant to translation, "
        "scale and rotation. They span many orders of magnitude, so they are log-scaled and clipped "
        "as in Equation (5.2), where \u03b7 is the raw invariant.",
    )
    equation(
        doc,
        [("h", {}), ("i", {"sub": True}), (" = \u2212", {}), ("sgn", UPRIGHT),
         ("(\u03b7", {}), ("i", {"sub": True}), (") \u00b7 ", {}), ("log", UPRIGHT),
         ("10", {"sub": True, "italic": False}), ("(|\u03b7", {}), ("i", {"sub": True}),
         ("| + 10", {}), ("\u221230", {"sup": True}), (")", {})],
        "5.2",
    )
    para(
        doc,
        "The contour is resampled to sixty-four equally spaced points and treated as a complex "
        "sequence z(n) = x(n) + j y(n). The magnitude of its discrete Fourier transform is a "
        "description of the outline that is independent of where the contour starts, and dividing by "
        "the first coefficient removes the remaining scale dependence, as in Equation (5.3).",
    )
    equation(
        doc,
        [("F", {}), ("k", {"sub": True}), (" = |Z", {}), ("k", {"sub": True}), ("| / |Z", {}),
         ("1", {"sub": True}), ("|,   k = 1, 2, \u2026, 20", {})],
        "5.3",
    )
    para(
        doc,
        "The radial signature describes the hand as a function of direction. The sixty-four "
        "resampled points are grouped into twenty-four angular bins around the centroid, and each "
        "bin reports the mean distance of its points from the centroid, normalised by the largest "
        "distance in the contour. Equation (5.4) states this, where B_j is the set of points whose "
        "angle falls in bin j and R is the largest distance from the centroid to any point. A "
        "spread hand produces a signature with several peaks; a fist produces a nearly constant one.",
    )
    equation(
        doc,
        [("r", {}), ("j", {"sub": True}), (" = ", {}), ("1 / |B", {}), ("j", {"sub": True}),
         ("| \u03a3", {}), ("i\u2208Bj", {"sub": True}), (" \u2016p", {}), ("i", {"sub": True}),
         (" \u2212 c\u2016 / R", {}), ("max", {"sub": True, "italic": False})],
        "5.4",
    )
    para(
        doc,
        "The four blocks are concatenated and passed through a final clean-up that replaces any "
        "non-finite value with zero. The vector length is asserted against the constant "
        "FEATURE_DIM, so a change to any block that is not accompanied by a version bump fails "
        "loudly rather than silently corrupting the model.",
    )

    h2(doc, "5.6", "Classification and Decision Logic")
    para(
        doc,
        "The classifier is a support vector machine with a radial basis function kernel, preceded by "
        "a standard scaler. The scaler is essential: solidity lies between zero and one while the "
        "log-scaled Hu moments can reach twenty, and without standardisation the kernel would be "
        "dominated by a handful of dimensions.",
    )
    equation(
        doc,
        [("f(x) = \u03a3", {}), ("i", {"sub": True}), (" \u03b1", {}), ("i", {"sub": True}),
         (" y", {}), ("i", {"sub": True}), (" K(x", {}), ("i", {"sub": True}),
         (", x) + b,   K(x, x\u2032) = exp(\u2212\u03b3\u2016x \u2212 x\u2032\u2016", {}),
         ("2", {"sup": True}), (")", {})],
        "5.5",
    )
    para(
        doc,
        "Equation (5.5) is the decision function. The hyperparameters in Table 5.3 were chosen by "
        "grid search on the held-out split and then frozen; the reported accuracy is from the same "
        "split, which is a limitation discussed in Chapter 7.",
    )
    table_caption(doc, "5.3", "Classifier configuration used for the reported model")
    table(
        doc,
        ["Parameter", "Value", "Reason"],
        [
            ("Kernel", "RBF", "Hand-shape classes are not linearly separable"),
            ("C", "8.0", "Allows moderate overlap without over-fitting"),
            ("gamma", "\u201cscale\u201d (1 / (n_features \u00d7 X.var()))", "Stable across feature versions"),
            ("probability", "True", "The interface shows a confidence value"),
            ("class_weight", "\u201cbalanced\u201d", "Compensates for unequal capture counts"),
            ("Pre-processing", "StandardScaler", "Puts all sixty-one dimensions on one scale"),
            ("Test size", "25 per cent, stratified", "At least two frames per class in the test set"),
            ("Random state", "42", "Reproducible split"),
        ],
        widths=[3.4, 6.0, 5.2],
        align="left",
        first_col_bold=True,
    )
    para(
        doc,
        "Prediction alone would produce a flickering transcript. Two filters sit between the "
        "classifier and the text. The first is a majority vote over the last nine frames, which "
        "removes single-frame errors without adding perceptible delay. The second is a hold rule: a "
        "letter is committed only when the smoothed label has remained stable and its probability "
        "has stayed above 0.55 for 1.5 seconds. After a commit, the same letter is suppressed until "
        "the hand leaves the frame or changes shape, so a held sign produces one letter rather than "
        "a stream of repeats.",
    )
    para(
        doc,
        "The same pipeline runs in the laboratory panel during capture. Each accepted frame is "
        "described, stored as a row of the class feature file, and saved as a small mask image. "
        "Training then loads all rows, fits the scaler and the SVC, evaluates on the held-out split, "
        "and refits on the full dataset before saving the bundle. The reported accuracy always comes "
        "from the held-out split, never from the refitted model.",
    )
