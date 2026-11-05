"""Chapters 7 and 8, and the annexures."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

import report_data as D
from report_lib import bullets, chapter, h2, h3, para, table, table_caption


def chapter7(doc) -> None:
    chapter(doc, 7, "Conclusion & Discussion")

    para(
        doc,
        "The project set out to find out whether a single webcam, a laptop processor and a modest "
        "dataset could read fingerspelled letters well enough to be useful, and whether such a "
        "system could be made transparent enough to teach from. Both questions have a positive "
        "answer, with qualifications that are more instructive than the headline accuracy.",
    )
    para(
        doc,
        f"The workbench recognises all twenty-six letters with {D.pct(D.ACCURACY)} accuracy on "
        f"{D.TEST_SAMPLES:,} held-out frames and runs at about thirty frames per second on the CPU. "
        "The classifier itself accounts for less than one millisecond per frame, which demonstrates "
        "that the classical route is not a compromise forced by hardware but a viable design for "
        "this problem. The descriptor is compact, every one of its sixty-one values has a geometric "
        "meaning, and the interface exposes the stages that produce it.",
    )
    para(
        doc,
        "The qualifications matter. The evaluation is within-session: frames from the same capture "
        "sessions appear on both sides of the split, so the number measures how well the model "
        "separates the recorded examples rather than how well it generalises to a new signer. The "
        "weakest classes are the closed-hand letters, where the silhouette is nearly identical and "
        "the distinguishing information lies inside the contour. The system recognises isolated "
        "letters, not continuous signing. These are not small caveats, and they define the next "
        "version of the work.",
    )

    h2(doc, "7.1", "Limitation of Project")
    table_caption(doc, "7.1", "Limitations of the present system")
    table(
        doc,
        ["Limitation", "Effect", "Evidence"],
        [
            ("Within-session evaluation", "Accuracy is optimistic for a new signer",
             "Stratified split mixes frames from the same sessions"),
            ("Small signer pool", "Skin range and hand proportions are not representative",
             "Six volunteers, one primary signer"),
            ("Closed-hand ambiguity", "B, C and D are the weakest classes",
             "Graph 6.2 and Graph 6.3"),
            ("Static letters only", "No movement, no grammar, no continuous signing",
             "Scope in Section 1.3"),
            ("Illumination sensitivity", "Skin range needs adjustment when the room changes",
             "Presets in Table 5.1"),
            ("Single hand", "Two-handed alphabets are not supported", "Segmentation keeps one contour"),
            ("No depth", "Overlapping fingers are invisible to the descriptor", "2-D contour only"),
            ("Development server", "Not hardened for a network deployment", "Flask development mode"),
        ],
        widths=[4.2, 6.0, 4.4],
        align="left",
        first_col_bold=True,
    )
    para(
        doc,
        "The first limitation is the most serious and deserves emphasis. A stratified split is the "
        "correct way to report performance on the captured distribution, but it does not answer the "
        "question a user will ask: will this work for me? A signer-independent protocol, in which "
        "every frame of a held-out volunteer is excluded from training, would give a lower and more "
        "honest number. That experiment is the first item of future work.",
    )

    h2(doc, "7.2", "Difficulties Encountered")
    para(doc, "Five difficulties consumed most of the debugging time.")
    bullets(
        doc,
        [
            ("The face competed with the hand. ", "Early versions segmented the face as a second "
             "skin blob, and when the hand passed near the chin the two merged into one contour. The "
             "fix, subtracting a Haar-detected face box before contour selection, was simple but "
             "took several days to diagnose because the failure was intermittent."),
            ("The first descriptor was too weak. ", "Solidity and defect count alone could not "
             "separate letters with the same number of extended fingers. Adding Hu moments, Fourier "
             "descriptors and the radial signature raised accuracy by more than fifteen percentage "
             "points."),
            ("The transcript repeated letters. ", "Without a suppression rule, holding a sign "
             "produced the same letter every 1.5 seconds. A commit latch that clears only when the "
             "shape changes fixed it."),
            ("Lighting changed between sessions. ", "Thresholds tuned in the evening failed in "
             "daylight. The presets are a pragmatic response; a adaptive method would be better."),
            ("Report figures drifted from the code. ", "Hand-made charts stopped matching the model "
             "after retraining. Generating every chart from the saved metrics file removed the "
             "possibility of drift."),
        ],
    )

    h2(doc, "7.3", "Future Enhancement Suggestions")
    para(
        doc,
        "The next version should be judged on signer-independent accuracy rather than on a random "
        "split. Table 7.2 lists the enhancements in the order in which they would be attempted.",
    )
    table_caption(doc, "7.2", "Planned enhancements, ordered by expected value")
    table(
        doc,
        ["Enhancement", "Why it matters", "Approach"],
        [
            ("Signer-independent evaluation", "Turns the accuracy into a claim about people, not frames",
             "Leave-one-volunteer-out protocol"),
            ("Landmark fusion", "Adds finger configuration that the silhouette cannot see",
             "Combine 61-D descriptor with 21 hand landmarks"),
            ("Adaptive skin model", "Removes the preset tuning burden",
             "Per-session colour histogram or Gaussian mixture"),
            ("Dynamic signs", "Moves from spelling to signing",
             "Temporal model over descriptor sequences"),
            ("Two-handed support", "Covers Indian Sign Language and others",
             "Track two contours and describe their relation"),
            ("On-device deployment", "Classroom and kiosk use without a laptop",
             "Quantised model on a single-board computer"),
            ("Word prediction", "Reduces the effort of spelling long words",
             "Character n-gram model over the transcript"),
            ("Accessibility audit", "Ensures the interface is usable by its intended users",
             "Testing with deaf participants and a screen reader"),
        ],
        widths=[4.4, 5.8, 4.4],
        align="left",
        first_col_bold=True,
    )
    para(
        doc,
        "The most valuable of these is not a modelling change but an evaluation change. A "
        "leave-one-volunteer-out protocol would tell the project what it currently cannot: whether "
        "the descriptor captures the geometry of a hand or the habits of the six people who recorded "
        "it. Until that experiment is run, the reported accuracy should be read as an upper bound.",
    )
    para(
        doc,
        "The work nevertheless leaves something usable behind. The workbench runs, the dataset "
        "exists, every figure in this report can be regenerated from the saved metrics, and the "
        "pipeline is simple enough that the next student can change one stage and see the effect on "
        "the same twenty-six classes. That combination, rather than the accuracy figure alone, is the "
        "contribution of the project.",
    )


def chapter8(doc) -> None:
    chapter(doc, 8, "Bibliography & References")

    para(
        doc,
        "References follow the IEEE numeric style and are cited in the text by bracketed number. "
        "Books are listed first, followed by papers, standards and software documentation.",
    )

    h2(doc, "8.1", "Reference Books")
    books = [
        "Gonzalez, R. C., & Woods, R. E. (2018). Digital image processing (4th ed.). Pearson.",
        "Szeliski, R. (2022). Computer vision: Algorithms and applications (2nd ed.). Springer. "
        "https://szeliski.org/Book/",
        "Bishop, C. M. (2006). Pattern recognition and machine learning. Springer.",
        "Hastie, T., Tibshirani, R., & Friedman, J. (2009). The elements of statistical learning "
        "(2nd ed.). Springer.",
        "Pressman, R. S., & Maxim, B. R. (2020). Software engineering: A practitioner's approach "
        "(9th ed.). McGraw-Hill.",
        "Sommerville, I. (2016). Software engineering (10th ed.). Pearson.",
        "Kumar, A. (2021). Computer vision with Python: A practical guide. BPB Publications.",
    ]
    for i, book in enumerate(books, start=1):
        p = doc.add_paragraph()
        p.add_run(f"[B{i}]  {book}")

    h2(doc, "8.2", "Other Documentation & Resources")
    refs = [
        "Krizhevsky, A., Sutskever, I., & Hinton, G. E. (2012). ImageNet classification with deep "
        "convolutional neural networks. Advances in Neural Information Processing Systems, 25, "
        "1097\u20131105.",
        "Pigou, L., Dieleman, S., Kindermans, P.-J., & Schrauwen, B. (2015). Sign language "
        "recognition using convolutional neural networks. In Proceedings of the IEEE Conference on "
        "Computer Vision and Pattern Recognition Workshops (pp. 20\u201328).",
        "Rastgoo, R., Kiani, K., & Escalera, S. (2021). Sign language recognition: A deep survey. "
        "Expert Systems with Applications, 164, 113794.",
        "Camgoz, N. C., Hadfield, S., Koller, O., & Bowden, R. (2018). Neural sign language "
        "translation. In Proceedings of the IEEE Conference on Computer Vision and Pattern "
        "Recognition (pp. 7784\u20137793).",
        "Zhang, F., Bazarevsky, V., Vakunov, A., Tkachenka, A., Sung, G., Chang, C.-L., & Grundmann, "
        "M. (2020). MediaPipe Hands: On-device real-time hand tracking. arXiv:2006.10214.",
        "Otsu, N. (1979). A threshold selection method from gray-level histograms. IEEE Transactions "
        "on Systems, Man, and Cybernetics, 9(1), 62\u201366.",
        "Hu, M.-K. (1962). Visual pattern recognition by moment invariants. IRE Transactions on "
        "Information Theory, 8(2), 179\u2013187.",
        "Cortes, C., & Vapnik, V. (1995). Support-vector networks. Machine Learning, 20(3), "
        "273\u2013297.",
        "Viola, P., & Jones, M. (2001). Rapid object detection using a boosted cascade of simple "
        "features. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition "
        "(Vol. 1, pp. 511\u2013518).",
        "Zuiderveld, K. (1994). Contrast limited adaptive histogram equalization. In P. S. Heckbert "
        "(Ed.), Graphics gems IV (pp. 474\u2013485). Academic Press.",
        "Starner, T., & Pentland, A. (1995). Real-time American Sign Language recognition from video "
        "using hidden Markov models. In Proceedings of the International Symposium on Computer "
        "Vision (pp. 265\u2013270).",
        "Cui, R., Liu, H., & Zhang, C. (2019). A deep neural framework for continuous sign language "
        "recognition by iterative training. IEEE Transactions on Multimedia, 21(7), 1880\u20131891.",
    ]
    for i, ref in enumerate(refs, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = None
        p.paragraph_format.first_line_indent = None
        p.add_run(f"[{i}]  {ref}")

    h3(doc, "8.2.1", "Software and Standards Consulted")
    extra = [
        "OpenCV. (2024). OpenCV 4.x documentation: Contours, convex hull and convexity defects. "
        "https://docs.opencv.org/",
        "scikit-learn developers. (2024). scikit-learn user guide: Support vector machines and "
        "model evaluation. https://scikit-learn.org/",
        "Pallets Projects. (2024). Flask documentation. https://flask.palletsprojects.com/",
        "Mozilla. (2024). MDN Web Docs: Web Speech API and Media Streams. https://developer.mozilla.org/",
        "World Health Organization. (2021). World report on hearing. WHO Press.",
    ]
    for text in extra:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = None
        p.add_run("\u2022  " + text)


def annexure1(doc) -> None:
    _annex_title(doc, "ANNEXURE I", "Per-sign evaluation results")
    para(
        doc,
        "Precision, recall and F1 are percentages; support is the number of held-out frames for the "
        "sign. The values are read directly from the saved model bundle and are the same values that "
        "the sign library in Figure 6.17 displays.",
    )
    rows = []
    for label in D.LABELS:
        m = D.PER_CLASS[label]
        rows.append((
            label,
            str(D.CLASS_COUNTS[label]),
            str(m["support"]),
            f"{m['precision'] * 100:.1f}",
            f"{m['recall'] * 100:.1f}",
            f"{m['f1'] * 100:.1f}",
        ))
    rows.append((
        "All",
        f"{D.SAMPLES:,}",
        f"{D.TEST_SAMPLES:,}",
        f"{D.ACCURACY * 100:.1f}",
        f"{D.ACCURACY * 100:.1f}",
        f"{D.WEIGHTED_F1 * 100:.1f}",
    ))
    table_caption(doc, "A1.1", "Held-out precision, recall and F1 for each sign")
    table(
        doc,
        ["Sign", "Frames", "Support", "Precision (%)", "Recall (%)", "F1 (%)"],
        rows,
        widths=[2.0, 2.4, 2.4, 3.0, 2.8, 2.4],
        align="center",
        font_size=8.5,
        first_col_bold=True,
        pad=0.55,
    )
    para(
        doc,
        "The final row reports the overall accuracy in the recall column and the weighted F1 in the "
        "F1 column, so that the totals are comparable with the per-sign figures above them.",
        italic=True,
        size=10,
    )


def annexure2(doc) -> None:
    _annex_title(doc, "ANNEXURE II", "Application interface and data layout")
    para(
        doc,
        "The workbench exposes a small JSON interface between the browser and the vision engine. "
        "Table A2.1 lists the routes; Table A2.2 lists the on-disk layout of the dataset and the "
        "model bundle.",
    )
    table_caption(doc, "A2.1", "HTTP routes exposed by the Flask application")
    table(
        doc,
        ["Method", "Route", "Purpose", "Returns"],
        [
            ("GET", "/", "Serve the workbench page", "HTML"),
            ("GET", "/video_feed", "Stream the annotated camera view", "MJPEG frames"),
            ("GET", "/api/state", "Snapshot of the live state", "JSON"),
            ("GET", "/api/stage/<name>.jpg", "One segmentation stage image", "JPEG"),
            ("POST", "/api/preset", "Change the skin preset", "JSON settings"),
            ("POST", "/api/skin", "Set custom HSV bounds", "JSON settings"),
            ("POST", "/api/collect", "Start or stop a capture run", "JSON progress"),
            ("POST", "/api/train", "Fit, evaluate and reload the model", "JSON metrics"),
            ("POST", "/api/reset", "Delete captures and model after confirmation", "JSON status"),
            ("POST", "/api/transcript", "Append, delete or clear text", "JSON transcript"),
        ],
        widths=[2.0, 4.2, 5.6, 2.8],
        align="left",
        font_size=9,
    )
    table_caption(doc, "A2.2", "On-disk layout of the project artefacts")
    table(
        doc,
        ["Path", "Contents"],
        [
            ("src/config.py", "Paths, camera settings, ROI, feature contract and skin presets"),
            ("src/segment.py", "Skin segmentation, face exclusion and stage images"),
            ("src/features.py", "The sixty-one dimensional descriptor"),
            ("src/classifier.py", "Training, evaluation, persistence and prediction"),
            ("src/dataset.py", "Feature and mask storage per label"),
            ("src/engine.py", "Camera thread, smoothing, hold rule and capture control"),
            ("dataset/<SIGN>/features.npy", "One row of sixty-one features per accepted frame"),
            ("dataset/<SIGN>/masks/*.png", "Stored 180 \u00d7 180 mask for each accepted frame"),
            ("dataset/<SIGN>/meta.json", "Label, feature version, sample count and timestamp"),
            ("models/sign_model.joblib", "Scaler, SVC, labels, metrics and confusion matrix"),
            ("models/settings.json", "Current skin preset and custom bounds"),
        ],
        widths=[6.2, 8.4],
        align="left",
        font_size=9,
    )


def _annex_title(doc, label: str, title: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(label)
    run.bold = True
    run.font.size = Pt(14)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(18)
    run2 = p2.add_run(title)
    run2.bold = True
    run2.font.size = Pt(13)
