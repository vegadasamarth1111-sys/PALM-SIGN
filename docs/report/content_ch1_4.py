"""Chapters 1 to 4."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

import report_data as D
from report_lib import bullets, chapter, figure, h2, h3, para, table, table_caption


def chapter1(doc) -> None:
    chapter(doc, 1, "Overview")

    para(
        doc,
        "A camera pointed at a hand is one of the cheapest sensors available to a software system, "
        "and a hand is one of the most expressive objects it will ever see. This project asks a "
        "narrow version of a large question: can a single ordinary webcam, a laptop processor and a "
        "dataset of a few thousand frames be enough to read the twenty-six fingerspelled letters of "
        "the American Manual Alphabet reliably enough to be useful? The answer documented in this "
        "report is a qualified yes, and the qualification is as interesting as the result.",
    )
    para(
        doc,
        "The system built for the study is called PALM/SIGN. It is a browser-based workbench rather "
        "than a single script: a live camera stage, a reading panel that shows the recognised letter "
        "and its confidence, an editable transcript, and a laboratory panel in which the skin range, "
        "the intermediate segmentation stages, the per-sign accuracy and the training controls are "
        "all visible. The name reflects the two halves of the problem, the palm as the physical "
        "object and the sign as the linguistic unit.",
    )

    h2(doc, "1.1", "Problem Statement")
    para(
        doc,
        "More than five per cent of the world's population lives with disabling hearing loss, and "
        "for a large part of that population a signed language is the first language, not a "
        "translation of a spoken one. In classrooms, clinics, ticket counters and family "
        "conversations, the absence of a signer is usually solved by writing on paper, typing on a "
        "phone, or by not communicating at all. Professional interpreters are scarce and expensive, "
        "and they are not available for the spontaneous, low-stakes exchanges that make up most of "
        "daily life.",
    )
    para(
        doc,
        "Fingerspelling is the part of a signed language that is used for names, place names, "
        "acronyms and technical vocabulary. It is a natural first target for automation because each "
        "letter is a static hand shape held for a moment, and because a fingerspelled word is "
        "already a sequence of discrete symbols. The technical problem is nevertheless difficult in "
        "the conditions that matter: a consumer webcam, indoor lighting that changes through the "
        "day, a hand that moves closer and further away, a face that is also skin-coloured and "
        "therefore competes with the hand for attention, and a user who expects an answer within a "
        "few hundred milliseconds.",
    )
    para(
        doc,
        "Existing approaches tend to solve the accuracy problem by making the deployment problem "
        "worse. Glove-based systems need hardware that costs more than the laptop. End-to-end "
        "convolutional models need tens of thousands of labelled images, a GPU for training and a "
        "large model file for inference. Commercial applications are closed, so a student cannot see "
        "why a letter was misread. The problem addressed here is therefore not only recognition "
        "accuracy but also transparency and cost: a system that a department can run on the "
        "computers it already owns, and whose intermediate stages can be inspected and explained.",
    )

    h2(doc, "1.2", "Objectives")
    para(doc, "The project pursues six objectives, each of which is verified later in the report.")
    bullets(
        doc,
        [
            ("Capture a usable dataset. ", "Record a balanced set of frames for all twenty-six "
             "letters using a single webcam and a repeatable desk setup."),
            ("Build a segmentation stage that survives real rooms. ", "Correct uneven illumination, "
             "isolate skin in HSV space, remove the face, and keep only the largest plausible hand "
             "contour."),
            ("Design a compact, scale-free descriptor. ", "Describe each hand shape with a fixed "
             "sixty-one dimensional vector built from geometric ratios, Hu moments, Fourier "
             "descriptors and a radial signature."),
            ("Train and evaluate a classifier honestly. ", "Fit a support vector machine and report "
             "accuracy on a stratified held-out split rather than on the training data."),
            ("Deliver a real-time workbench. ", "Stream the annotated camera view to a browser, "
             "commit letters with a hold rule, and provide capture, train and reset controls."),
            ("Make the system explainable. ", "Expose the skin range, the segmentation stages, the "
             "per-sign recall and the confusion matrix so that a reader can audit the behaviour."),
        ],
    )

    h2(doc, "1.3", "Scope")
    para(doc, "The scope is deliberately narrow so that the evaluation can be honest.")
    para(doc, "In scope:", bold=True, space_after=2)
    bullets(
        doc,
        [
            "Static, one-handed fingerspelling of the twenty-six letters A to Z of the American "
            "Manual Alphabet.",
            "A single frontal USB webcam at 640 \u00d7 480 resolution and thirty frames per second.",
            "One user at a time, seated at a desk, with the hand inside a marked region of interest.",
            "Recognition and transcription on a laptop CPU, with no network service and no GPU.",
            "A local web application that runs on the same machine as the camera.",
        ],
    )
    para(doc, "Out of scope:", bold=True, space_after=2)
    bullets(
        doc,
        [
            "Dynamic or movement-based signs, grammatical facial expression and continuous signing.",
            "Two-handed alphabets and the Indian Sign Language variants that use both hands.",
            "Speaker-independent evaluation across many users and skin tones; the present dataset "
            "comes from a small group of volunteers.",
            "Translation into spoken language, speech synthesis beyond the browser's own voice, and "
            "any cloud deployment.",
        ],
    )
    para(
        doc,
        "These exclusions are not claims that the excluded problems are unimportant. They mark the "
        "boundary within which the measured numbers in Chapter 6 should be read.",
    )

    h2(doc, "1.4", "Platform Specification")
    para(
        doc,
        "The workbench was developed and evaluated on a single laptop with an integrated webcam. "
        "The specification below is the machine on which the reported frame rate and training times "
        "were measured; the software itself has no unusual dependency and runs on any recent "
        "Windows, Linux or macOS computer with a USB camera.",
    )

    h3(doc, "1.4.1", "Hardware")
    table_caption(doc, "1.1", "Development and evaluation hardware")
    table(
        doc,
        ["Component", "Specification", "Role in the project"],
        [
            ("Laptop", "Intel Core i5, 4 cores, 16 GB RAM", "Runs the camera loop, the classifier and the Flask server"),
            ("Camera", "Integrated 720p webcam, used at 640 \u00d7 480", "Captures the training frames and the live stream"),
            ("Display", "1920 \u00d7 1080, 60 Hz", "Browser view of the workbench"),
            ("Lighting", "9 W diffused desk lamp, front-left", "Repeatable illumination for capture"),
            ("Mount", "Tripod at approximately 55 cm from the hand", "Keeps the field of view stable between sessions"),
            ("Storage", "256 GB SSD", "Dataset, model bundle and report artefacts"),
        ],
        widths=[3.0, 5.4, 6.2],
        align="left",
        first_col_bold=True,
    )

    h3(doc, "1.4.2", "Software")
    table_caption(doc, "1.2", "Software stack and versions used for the reported results")
    table(
        doc,
        ["Layer", "Software", "Purpose"],
        [
            ("Operating system", "Windows 11", "Host platform"),
            ("Language", "Python 3.11", "All vision, learning and server code"),
            ("Vision", "OpenCV 4.x", "Capture, colour conversion, morphology, contours, hull"),
            ("Numerics", "NumPy", "Array algebra and the feature vector"),
            ("Learning", "scikit-learn", "StandardScaler, SVC, stratified split, metrics"),
            ("Persistence", "joblib", "Model bundle serialisation"),
            ("Web", "Flask", "HTTP routes and the MJPEG video feed"),
            ("Front end", "HTML5, CSS3, vanilla JavaScript", "Desk, transcript and laboratory panel"),
            ("Documentation", "python-docx, Matplotlib", "This report and its figures"),
        ],
        widths=[3.2, 5.2, 6.2],
        align="left",
        first_col_bold=True,
    )

    h3(doc, "1.4.3", "Implementation Language")
    para(
        doc,
        "Python was chosen because the whole pipeline, from reading a camera frame to fitting a "
        "classifier, can be expressed in one language with mature libraries. OpenCV exposes the "
        "contour and convex-hull primitives that the descriptor depends on; scikit-learn provides a "
        "well-tested support vector implementation and the metric functions used for evaluation; "
        "Flask serves both JSON state and an MJPEG stream with very little code. The front end is "
        "deliberately written in plain JavaScript rather than a framework, so that the repository "
        "has no build step and can be opened on a laboratory machine without installing Node.js.",
    )

    figure(doc, D.fig("1.1"), "1.1",
           "Development methodology followed for the project, including the accuracy gate that "
           "returns control to feature engineering", width_cm=10.2)
    para(
        doc,
        "Figure 1.1 shows the sequence that was actually followed. The dashed return path is not "
        "decoration: the first descriptor, built only from solidity and the defect count, stalled "
        "below eighty per cent, and the project only moved forward after the Fourier and radial "
        "components were added.",
    )

    figure(doc, D.fig("1.2"), "1.2",
           "Conceptual framework: acquisition, representation, recognition and presentation, with "
           "the dataset store feeding both capture and training", width_cm=12.8)
    para(
        doc,
        "The conceptual framework in Figure 1.2 treats the dataset as a first-class part of the "
        "system rather than as an input that appears from nowhere. Every frame that the classifier "
        "learns from is produced by the same acquisition and representation stages that run live, "
        "which is why the laboratory panel can show the capture count next to the accuracy of each "
        "sign.",
    )


def chapter2(doc) -> None:
    chapter(doc, 2, "System Analysis")

    h2(doc, "2.1", "Identification of Need")
    para(
        doc,
        "The need was identified through three small studies rather than assumed. First, six "
        "volunteers with no signing experience were asked to spell a short word using only a printed "
        "alphabet chart while a second person tried to read it; all six found the exercise slow, and "
        "four asked for a written alternative within the first minute. Second, a short conversation "
        "with two special-education teachers confirmed that fingerspelling practice is a recurring "
        "classroom activity for which no inexpensive feedback tool exists. Third, a review of "
        "available software showed that most free tools are either mobile keyboards with no "
        "recognition or closed applications that cannot be inspected or extended.",
    )
    para(
        doc,
        "The common thread is not a demand for a better alphabet chart but for immediate, private "
        "feedback: the signer wants to know whether the hand shape was read correctly, and the "
        "reader wants a text record that can be edited and spoken aloud. That pair of needs shaped "
        "the interface more than any single recognition technique.",
    )
    table_caption(doc, "2.1", "Stakeholder needs translated into system requirements")
    table(
        doc,
        ["Stakeholder", "Observed need", "Requirement derived"],
        [
            ("Deaf or hard-of-hearing user", "Private, immediate transcription without an interpreter",
             "Local, offline recognition with a visible confidence value"),
            ("Hearing conversation partner", "A readable, editable record of what was signed",
             "Transcript panel with space, delete, clear, copy and speak"),
            ("Teacher or trainer", "Evidence of which letters are confused",
             "Per-sign accuracy, confusion matrix and stage inspection"),
            ("Student developer", "A system that can be understood and modified",
             "Classic, documented features and a single-file Flask back end"),
            ("Department", "No recurring cost and no special hardware",
             "CPU-only inference, open-source stack, ordinary webcam"),
        ],
        widths=[4.0, 5.2, 5.4],
        align="left",
        first_col_bold=True,
    )

    h2(doc, "2.2", "Preliminary Investigation")
    para(
        doc,
        "Three sensing options were compared before any code was written. A sensor glove gives "
        "joint angles directly and is the most accurate option for finger configuration, but a "
        "usable glove costs tens of thousands of rupees, needs calibration and is tethered. A depth "
        "camera such as a structured-light sensor gives a clean hand silhouette and is robust to "
        "skin colour, but it adds hardware, fails in direct sunlight and is not present on ordinary "
        "laptops. A single RGB webcam is already present on every machine, needs no calibration and "
        "costs nothing, at the price of having to solve segmentation in software.",
    )
    para(
        doc,
        "The webcam was selected, and the investigation then turned to the representation. A pilot "
        "capture of three letters, eighty frames each, was used to compare two baselines: a "
        "downsampled raw-pixel classifier and a small set of hand-crafted shape ratios. The "
        "raw-pixel baseline reached only sixty-one per cent on held-out frames because it learned "
        "the position of the hand in the frame rather than its shape. The shape ratios generalised "
        "far better, which settled the direction of the project: describe the geometry of the "
        "contour, not the pixels.",
    )
    para(
        doc,
        "The pilot also exposed two practical problems that shaped the design. Skin-coloured walls "
        "and wooden furniture produced large false contours, so the region of interest was narrowed "
        "to the right half of the frame where the hand is held. Faces produced a second skin blob "
        "that sometimes merged with the hand, so a Haar cascade was added to subtract the face "
        "before the largest contour is chosen.",
    )
    figure(doc, D.fig("2.1"), "2.1",
           "Experimental setup: webcam on a tripod, hand inside the marked region of interest, "
           "diffused front light and a plain background", width_cm=13.6)
    para(
        doc,
        "Figure 2.1 is the arrangement used for every capture session in the dataset. The lamp is "
        "placed front-left so that the fingers cast a soft shadow away from the camera, and the "
        "background is a plain wall rather than a skin-coloured surface. The setup is modest on "
        "purpose: if the system needed a studio, it would not be usable in a classroom.",
    )


def chapter3(doc) -> None:
    chapter(doc, 3, "Feasibility Study")

    para(
        doc,
        "A feasibility study was carried out on three axes: whether the system could be built with "
        "the available skills and hardware, whether it made economic sense, and whether it could be "
        "operated by the people for whom it is intended.",
    )

    h2(doc, "3.1", "Technical Feasibility")
    para(
        doc,
        "Every stage of the pipeline maps onto a well-supported library function. Capture and "
        "colour conversion are single OpenCV calls; adaptive histogram equalisation is provided as "
        "CLAHE; skin segmentation is an in-range test in HSV; the face detector is a Haar cascade "
        "that ships with OpenCV; contour extraction, convex hull and convexity defects are all "
        "primitives of the same library. The descriptor is ordinary NumPy arithmetic, and the "
        "classifier is a support vector machine that scikit-learn fits in about two seconds on the "
        "full dataset.",
    )
    para(
        doc,
        "The demanding requirement is latency. The live loop must segment, describe and classify a "
        "frame thirty times per second while also serving an MJPEG stream. Measurement showed that "
        "segmentation and feature extraction together take roughly twelve milliseconds per frame on "
        "the development laptop, and that a single prediction from the trained SVC takes under one "
        "millisecond. The remaining budget is spent on encoding and streaming. The target of thirty "
        "frames per second is therefore technically reachable without a GPU.",
    )
    para(
        doc,
        "The principal technical risk is illumination. HSV thresholds that work under a desk lamp "
        "fail near a window in the afternoon, which is why the skin range is exposed in the "
        "laboratory panel with three presets and a fine-tuning control rather than being fixed in "
        "code.",
    )

    h2(doc, "3.2", "Economical Feasibility")
    para(
        doc,
        "The software cost of the project is zero: Python, OpenCV, NumPy, scikit-learn, Flask and "
        "the browser are all free and open source, and the model is small enough to be stored in a "
        "single file. The hardware cost is limited to a webcam if the laptop does not already have "
        "one, and to a desk lamp. Table 3.1 compares the indicative cost of the chosen approach with "
        "the alternatives considered during the preliminary investigation.",
    )
    table_caption(doc, "3.1", "Indicative cost comparison of the sensing options considered")
    table(
        doc,
        ["Option", "One-time cost (INR)", "Recurring cost", "Notes"],
        [
            ("Sensor glove", "35,000 \u2013 80,000", "Calibration time, replacement sensors", "Accurate finger angles, tethered"),
            ("Depth camera", "18,000 \u2013 35,000", "None", "Clean silhouette, extra hardware"),
            ("RGB webcam (chosen)", "0 \u2013 2,500", "None", "Already present on most laptops"),
            ("Human interpreter", "0", "500 \u2013 1,500 per hour", "Not available on demand"),
            ("Manual typing", "0", "Time", "No signing required, breaks the conversation"),
        ],
        widths=[3.6, 3.4, 4.0, 3.6],
        align="center",
        first_col_bold=True,
    )
    para(
        doc,
        "The comparison is not a claim that a webcam matches a glove in accuracy. It is a claim "
        "about the marginal cost of the first useful version: for a department that already owns "
        "laptops, the webcam route costs nothing and can be deployed the same day.",
    )

    h2(doc, "3.3", "Operational Feasibility")
    para(
        doc,
        "Operationally the system is a single command. The server starts, prints the local address, "
        "and the user opens that address in a browser; no installation, account or network "
        "connection is required on the client side. The desk view is designed to be read at a "
        "glance: the current letter is large, the confidence is a bar rather than a number alone, "
        "and the transcript behaves like a text field. The laboratory panel is deliberately hidden "
        "behind one button so that a first-time user is not confronted with HSV sliders.",
    )
    para(
        doc,
        "The training workflow is also operable by a non-programmer. The user types a label, sets a "
        "frame count, presses start, holds the sign, and presses train. The interface reports the "
        "number of frames captured and the resulting held-out accuracy. Because the model is "
        "refitted from the stored features, no separate data-science tool is needed.",
    )
    table_caption(doc, "3.2", "Summary of the feasibility assessment")
    table(
        doc,
        ["Dimension", "Finding", "Verdict"],
        [
            ("Technical", "All stages map to stable libraries; CPU inference meets the frame budget", "Feasible"),
            ("Economical", "No software cost; hardware limited to a webcam and a lamp", "Feasible"),
            ("Operational", "One command, browser client, in-app capture and training", "Feasible"),
            ("Schedule", "Twelve weeks including capture, tuning and writing", "Feasible with buffer"),
            ("Main risk", "Illumination and skin-tone variation", "Mitigated, not eliminated"),
        ],
        widths=[3.4, 9.2, 2.4],
        align="left",
        first_col_bold=True,
    )


def chapter4(doc) -> None:
    chapter(doc, 4, "Literature Survey")

    para(
        doc,
        "Hand-shape recognition has been studied for more than three decades, and the literature "
        "divides cleanly by what is sensed and what is learned. This chapter summarises the strands "
        "that shaped the present design, states the benefits that follow from them, and positions "
        "the proposed solution among them.",
    )

    h2(doc, "4.1", "Work Done by Others")

    h3(doc, "4.1.1", "Glove and sensor-based recognition")
    para(
        doc,
        "The earliest practical systems instrumented the hand itself. Starner and Pentland [11] used "
        "a coloured glove and hidden Markov models to recognise American Sign Language sentences in "
        "real time, establishing the sequence-model view of signing that still dominates the field. "
        "Glove systems remain the most accurate way to measure finger configuration, but the "
        "hardware cost and the calibration burden keep them out of everyday use.",
    )

    h3(doc, "4.1.2", "Appearance-based static recognition")
    para(
        doc,
        "With the arrival of large image datasets and GPU training, appearance-based methods became "
        "dominant. Krizhevsky et al. [1] showed that a deep convolutional network could learn "
        "hierarchical image features from raw pixels, and Pigou et al. [2] applied a similar "
        "architecture to sign language recognition with promising results on a small vocabulary. "
        "The attraction is that no hand-crafted descriptor is needed; the cost is that tens of "
        "thousands of labelled images and a GPU are needed to train one.",
    )
    para(
        doc,
        "Classical descriptors did not disappear. Otsu [6] and the moment invariants of Hu [7] "
        "remain the standard tools for shape description when data are scarce, and the Fourier "
        "descriptor of a closed contour is still one of the most compact ways to describe a hand "
        "outline. The present project belongs to this classical tradition, not because deep learning "
        "is unsuitable but because the dataset available to a single student is small.",
    )

    h3(doc, "4.1.3", "Landmark-based methods")
    para(
        doc,
        "A third strand bypasses segmentation entirely. MediaPipe Hands [5] predicts twenty-one "
        "three-dimensional hand landmarks on the device in real time, and many recent sign "
        "recognition systems feed those landmarks to a small classifier. The approach is robust to "
        "skin colour and background because it never segments skin. Its weakness for this project is "
        "pedagogical: the landmark model is itself a large learned component, so the workbench would "
        "explain less of the pipeline to a student.",
    )

    h3(doc, "4.1.4", "Sequence models and continuous signing")
    para(
        doc,
        "Camgoz et al. [4] formulated continuous sign language translation as a sequence-to-sequence "
        "problem, and Cui et al. [12] introduced iterative training for continuous recognition. "
        "Rastgoo et al. [3] survey the field and note that isolated recognition is largely solved for "
        "controlled capture, while continuous, signer-independent recognition remains open. These "
        "results set the long-term direction of the work described here, even though the present "
        "scope stops at isolated letters.",
    )

    h3(doc, "4.1.5", "Classical segmentation pipelines")
    para(
        doc,
        "The image-processing components used here are older than the learning literature and just "
        "as important. Viola and Jones [9] introduced the cascade of Haar features that still "
        "provides fast frontal face detection, and Zuiderveld [10] described contrast-limited "
        "adaptive histogram equalisation, which is used in this project to normalise uneven "
        "lighting. Cortes and Vapnik [8] formulated the soft-margin support vector machine whose "
        "RBF variant classifies the descriptor.",
    )

    figure(doc, D.fig("4.1"), "4.1",
           "Chronology of the approaches reviewed, from glove-based sequence models to the classical "
           "descriptor used in this project", width_cm=14.2)
    para(
        doc,
        "Figure 4.1 places the project on that timeline. It does not sit at the frontier of accuracy; "
        "it sits at the frontier of explainability and cost, which is the gap this report addresses.",
    )

    table_caption(doc, "4.1", "Comparison of representative hand-sign recognition approaches")
    table(
        doc,
        ["Study", "Sensing", "Representation", "Reported strength", "Limitation for this project"],
        [
            ("Starner & Pentland [11]", "Coloured glove", "Sensor stream + HMM", "Real-time sentences", "Requires instrumented glove"),
            ("Pigou et al. [2]", "RGB camera", "CNN on raw images", "Learns features automatically", "Needs large labelled set and GPU"),
            ("Krizhevsky et al. [1]", "RGB images", "Deep CNN", "Strong image features", "General vision, not sign-specific"),
            ("MediaPipe Hands [5]", "RGB camera", "21 3-D landmarks", "Skin- and background-robust", "Opaque learned component"),
            ("Camgoz et al. [4]", "Video", "Sequence-to-sequence network", "Continuous translation", "Very large model and corpus"),
            ("Cui et al. [12]", "Video", "Iterative deep framework", "Continuous recognition", "Training complexity"),
            ("PALM/SIGN (this work)", "RGB webcam", "61-D shape descriptor + RBF SVC", "Explainable, CPU real time, 6,983 frames", "Static letters, small signer pool"),
        ],
        widths=[3.4, 2.6, 3.6, 3.0, 3.6],
        align="left",
        font_size=8.5,
    )

    h2(doc, "4.2", "Benefits")
    para(doc, "The survey suggests four benefits that a classical, shape-based workbench can offer.")
    bullets(
        doc,
        [
            ("Low data requirement. ", "A few hundred frames per class are enough to train a usable "
             "model, which makes the project reproducible by a single student in one semester."),
            ("Transparency. ", "Every number in the feature vector has a geometric meaning, so a "
             "misclassification can be explained by pointing at a measurement rather than at an "
             "opaque activation."),
            ("CPU real time. ", "Inference costs under a millisecond, so the application runs on the "
             "same laptop that serves the browser."),
            ("Low cost and low friction. ", "No glove, no depth sensor and no cloud account; the "
             "camera that is already in the laptop is the sensor."),
        ],
    )

    h2(doc, "4.3", "Proposed Solution")
    para(
        doc,
        "The proposed solution is a complete workbench built around a classical shape descriptor. A "
        "frame is corrected, segmented, cleared of the face, reduced to a contour and described by "
        "sixty-one numbers. A support vector machine classifies the vector, and a temporal filter "
        "converts per-frame probabilities into committed letters. The browser shows the live stage, "
        "the reading, the transcript and a laboratory panel for inspection and retraining.",
    )
    para(doc, "The contributions of the work are therefore:")
    bullets(
        doc,
        [
            "A compact descriptor that combines defect geometry, Hu moments, Fourier descriptors and "
            "a radial signature in a fixed-length, scale-free vector.",
            "A segmentation stage that subtracts the face before contour selection, which removes a "
            "failure mode common in skin-based hand tracking.",
            "A held-out evaluation on 6,983 frames across twenty-six classes, reported per sign "
            "rather than as a single number.",
            "An inspectable browser workbench that exposes the intermediate stages and allows the "
            "model to be retrained from the interface.",
        ],
    )

    h2(doc, "4.4", "Technology Used")
    para(
        doc,
        "Table 4.2 lists the technologies and the specific reason each was selected. The stack is "
        "deliberately small; every dependency earns its place by removing a large amount of code "
        "that would otherwise have to be written and tested.",
    )
    table_caption(doc, "4.2", "Technology stack and the reason for each choice")
    table(
        doc,
        ["Technology", "Version", "Used for", "Why this choice"],
        [
            ("Python", "3.11", "All application code", "One language for vision, learning and web"),
            ("OpenCV", "4.x", "Capture, colour, morphology, contours", "Mature primitives, fast enough on CPU"),
            ("NumPy", "1.26+", "Feature algebra", "Vectorised arithmetic and stable arrays"),
            ("scikit-learn", "1.4+", "Scaler, SVC, split, metrics", "Reliable implementations and metrics"),
            ("joblib", "1.3+", "Model persistence", "Stores NumPy arrays efficiently"),
            ("Flask", "3.x", "HTTP routes and MJPEG", "Minimal server with no build step"),
            ("HTML / CSS / JS", "Living standard", "Desk and laboratory interface", "No framework, no bundler"),
            ("Matplotlib", "3.8+", "Report figures", "Reproducible charts from the metrics file"),
        ],
        widths=[3.2, 2.6, 4.6, 4.2],
        align="left",
        font_size=9,
        first_col_bold=True,
    )
