"""Chapter 6: Software Engineering Approach."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH

import report_data as D
from report_lib import (bullets, chapter, figure, graph, h2, h3, para, table,
                        table_caption)


def chapter6(doc) -> None:
    chapter(doc, 6, "Software Engineering Approach")

    para(
        doc,
        "A computer-vision project can be written as a notebook and still produce a good accuracy "
        "number, but it cannot be handed to another student, tested systematically or extended. "
        "This chapter treats PALM/SIGN as a software system: it states the process model, derives "
        "requirements, plans the work, models the design in UML, describes the implementation and "
        "reports the tests.",
    )

    # ------------------------------------------------------------------ 6.1
    h2(doc, "6.1", "Software Engineering Paradigm Applied")
    h3(doc, "6.1.1", "Description")
    para(
        doc,
        "An incremental and iterative model was used. Four increments were planned, each of which "
        "produced something that could be run and judged: a camera loop with segmentation, a "
        "descriptor with a trained classifier, a live desk with a transcript, and finally the "
        "capture, training and reset controls with the metrics panel. Each increment passed through "
        "the same small cycle of requirement, design, implementation and testing, and each cycle "
        "began from what the previous demonstration had exposed.",
    )
    figure(doc, D.fig("6.1"), "6.1",
           "Incremental and iterative process applied to the project, with four delivered increments",
           width_cm=13.2)
    para(
        doc,
        "Figure 6.1 shows the cycle and the four increments. The iteration arrow is not a formality: "
        "the segmentation design changed twice after the first increment, and the descriptor changed "
        "once after the second, when the accuracy gate in Figure 1.1 was not met.",
    )

    h3(doc, "6.1.2", "Advantages & Disadvantages")
    para(doc, "Advantages observed in practice:", bold=True, space_after=2)
    bullets(
        doc,
        [
            "A working system existed from the third week, so failures in segmentation were found by "
            "using the system rather than by reading the code.",
            "Requirements could be refined against evidence; the stage inspector, for example, was "
            "added only after a demonstration made it obvious that a black-box result was not "
            "convincing.",
            "Risk was spread. The classifier was the least certain part, and it was isolated in the "
            "second increment behind a fixed feature contract.",
        ],
    )
    para(doc, "Disadvantages observed:", bold=True, space_after=2)
    bullets(
        doc,
        [
            "Refactoring cost. The engine was rewritten once when capture and live recognition began "
            "to share state, which consumed about a week.",
            "Documentation drift. Early diagrams described an architecture that no longer existed by "
            "the fourth increment and had to be redrawn.",
            "Scope pressure. Because each increment was demonstrable, it was tempting to add "
            "interface features before the evaluation was complete.",
        ],
    )

    h3(doc, "6.1.3", "Reasons for use")
    para(
        doc,
        "The deciding factor was uncertainty. At the start it was not known whether a skin-based "
        "segmentation would survive the available room, nor whether a sixty-one dimensional "
        "descriptor could separate twenty-six classes. A waterfall plan would have committed to a "
        "design before either question was answered. An incremental model allowed the pipeline to be "
        "built in the order in which the unknowns could be retired, and it produced the artefacts "
        "needed for this report as a by-product of each increment.",
    )

    # ------------------------------------------------------------------ 6.2
    h2(doc, "6.2", "Requirement Analysis")
    h3(doc, "6.2.1", "Software Requirements Specification")
    para(
        doc,
        "The requirements below are written from the point of view of a user at the desk. Each "
        "functional requirement has an identifier that is referenced by the test cases in Section "
        "6.6.2.",
    )
    table_caption(doc, "6.1", "Functional requirements")
    table(
        doc,
        ["ID", "Requirement", "Priority"],
        [
            ("FR1", "The system shall open the camera and display a live, mirrored view in the browser.", "High"),
            ("FR2", "The system shall segment the hand, remove the face and keep the largest hand contour.", "High"),
            ("FR3", "The system shall display the recognised letter and a confidence value for every frame.", "High"),
            ("FR4", "The system shall commit a letter only after the smoothed label holds for 1.5 seconds.", "High"),
            ("FR5", "The system shall maintain an editable transcript with space, delete, clear and copy.", "High"),
            ("FR6", "The system shall speak the transcript using the browser speech API.", "Medium"),
            ("FR7", "The system shall let the user switch between daylight, room-light and low-light skin presets.", "Medium"),
            ("FR8", "The system shall expose the four segmentation stages for inspection.", "Medium"),
            ("FR9", "The system shall capture a labelled set of frames and append it to the dataset.", "High"),
            ("FR10", "The system shall train the classifier, report held-out accuracy and reload the model.", "High"),
            ("FR11", "The system shall show frame count and held-out recall for every sign.", "Medium"),
            ("FR12", "The system shall reset captures and model only after explicit confirmation.", "Low"),
        ],
        widths=[1.6, 10.8, 2.2],
        align="left",
        font_size=9,
    )

    h3(doc, "6.2.1.1", "Glossary")
    table_caption(doc, "6.2", "Glossary of project-specific terms")
    table(
        doc,
        ["Term", "Meaning in this report"],
        [
            ("Commit", "Append a letter to the transcript after the hold rule is satisfied"),
            ("Confidence", "Probability reported by the SVC for the winning class"),
            ("Defect", "A convexity defect, the valley between two extended fingers"),
            ("Frame", "One 640 \u00d7 480 image captured from the camera"),
            ("Hull", "The smallest convex polygon that contains the hand contour"),
            ("Label", "One of the twenty-six classes, A to Z"),
            ("Reading", "The current smoothed label and its confidence, before commitment"),
            ("ROI", "Region of interest; the right half of the frame where the hand is held"),
            ("Sign", "A static hand shape representing one letter"),
            ("Stage", "One intermediate image of the pipeline shown in the laboratory panel"),
            ("Transcript", "The committed text that the user can edit or speak"),
        ],
        widths=[3.2, 11.2],
        align="left",
        first_col_bold=True,
    )

    h3(doc, "6.2.1.2", "Supplementary Specifications")
    para(
        doc,
        "The non-functional requirements constrain how well the functional behaviour must be "
        "delivered. They were measured rather than assumed wherever possible.",
    )
    table_caption(doc, "6.3", "Non-functional requirements")
    table(
        doc,
        ["ID", "Category", "Requirement", "Verification"],
        [
            ("NFR1", "Performance", "Live view at 25 frames per second or better", "FPS readout in the desk view"),
            ("NFR2", "Latency", "Reading updates within 200 ms of a change of sign", "Observed during testing"),
            ("NFR3", "Accuracy", "Held-out accuracy of at least 95 per cent", "Training report"),
            ("NFR4", "Usability", "A first-time user can read a letter without instructions", "Informal walkthrough"),
            ("NFR5", "Portability", "Runs on Windows, Linux and macOS with a USB camera", "Dependency review"),
            ("NFR6", "Offline", "No network access is required after installation", "Run with network disabled"),
            ("NFR7", "Robustness", "A missing camera produces a message, not a crash", "Camera unplugged during run"),
            ("NFR8", "Maintainability", "Feature dimension changes fail loudly", "Version check in the classifier"),
            ("NFR9", "Privacy", "No frame leaves the machine", "Code review; no outbound calls"),
        ],
        widths=[1.5, 2.6, 7.2, 3.3],
        align="left",
        font_size=9,
    )

    h3(doc, "6.2.1.3", "Use Case Model")
    para(
        doc,
        "Figure 6.2 shows the actors and the use cases. The user is the primary actor; the webcam is "
        "a supporting actor that participates in live reading and in capture. The laboratory use "
        "cases are drawn inside the same boundary because they are reached from the same page.",
    )
    figure(doc, D.fig("6.2"), "6.2",
           "Use case diagram of the workbench", width_cm=12.6)
    table_caption(doc, "6.4", "Use case descriptions for the three principal scenarios")
    table(
        doc,
        ["Use case", "Actor", "Precondition", "Main flow", "Postcondition"],
        [
            ("Read a sign", "User, webcam", "Server running, camera open",
             "Hold hand in ROI; system segments, describes and classifies; reading appears",
             "Letter shown with confidence; committed after 1.5 s"),
            ("Capture frames", "User, webcam", "Model may or may not exist",
             "Open lab, enter label and count, start; system stores features and masks until target",
             "Dataset grows by the requested number of frames"),
            ("Train model", "User", "At least two labels with ten frames each",
             "Press train; system fits scaler and SVC, evaluates, refits and reloads",
             "New bundle saved; accuracy and per-sign recall refreshed"),
        ],
        widths=[2.6, 2.4, 3.2, 4.4, 2.8],
        align="left",
        font_size=8.5,
        first_col_bold=True,
    )

    h3(doc, "6.2.2", "Conceptual Level Activity Diagram")
    para(
        doc,
        "The conceptual activity diagram in Figure 6.3 describes the live loop without committing to "
        "classes or threads. It is deliberately simple: capture, test for a hand, describe, classify, "
        "test the hold condition and either commit or keep reading.",
    )
    figure(doc, D.fig("6.3"), "6.3",
           "Conceptual activity diagram of the live recognition loop", width_cm=11.4)

    h3(doc, "6.2.3", "Conceptual Level Sequence Diagram")
    para(
        doc,
        "Figure 6.4 shows the messages exchanged during one poll of the desk. The browser asks the "
        "server for state; the engine takes a snapshot under its lock; the segmentation and "
        "classification results that the camera thread has already computed are returned as JSON. "
        "The video itself travels on a separate stream, so a slow poll never stalls the image.",
    )
    figure(doc, D.fig("6.4"), "6.4",
           "Conceptual sequence diagram for the live recognition loop", width_cm=14.0)

    # ------------------------------------------------------------------ 6.3
    h2(doc, "6.3", "Planning Managerial Issues")
    h3(doc, "6.3.1", "Planning Scope")
    para(
        doc,
        "The plan covered twelve weeks, from the first literature search to the submission of this "
        "report. Four work packages were defined: capture and dataset, vision pipeline, classifier "
        "and evaluation, and the web workbench. Report writing ran in parallel from week eight so "
        "that the figures were produced from the same scripts that generated the results.",
    )
    h3(doc, "6.3.2", "Project Resources")
    table_caption(doc, "6.5", "Resources used by the project")
    table(
        doc,
        ["Resource", "Quantity", "Use"],
        [
            ("Student effort", "About 18 hours per week for 12 weeks", "All work packages"),
            ("Mentor reviews", "8 scheduled reviews", "Direction, evaluation design, report review"),
            ("Laptop", "1", "Development, training and demonstration"),
            ("USB webcam", "1 (integrated)", "Capture and live recognition"),
            ("Desk lamp", "1", "Repeatable illumination"),
            ("Volunteers", "6", "Dataset capture and informal usability feedback"),
            ("Software", "Open-source stack", "No licence cost"),
        ],
        widths=[4.0, 5.6, 5.0],
        align="left",
        first_col_bold=True,
    )
    h3(doc, "6.3.3", "Team Organization")
    para(
        doc,
        "The project was a single-student effort, so the roles usually distributed across a team were "
        "held by one person in sequence rather than in parallel. The student acted as developer, data "
        "collector, tester and technical writer. The mentor acted as client representative and "
        "reviewer. This concentration is a risk in itself, because a single point of failure can "
        "delay every work package; it was mitigated by keeping each increment demonstrable and by "
        "committing working code before starting the next one.",
    )
    h3(doc, "6.3.4", "Project Scheduling")
    figure(doc, D.fig("6.5"), "6.5",
           "Project schedule across twelve weeks, showing overlapping work packages", width_cm=14.0)
    para(
        doc,
        "Figure 6.5 shows the schedule that was actually followed. Capture overlapped with the "
        "segmentation work because the pipeline could be tested on the frames that were being "
        "collected. Testing and tuning occupied the last three weeks and overlapped with report "
        "writing, which is why the evaluation figures and the report figures come from one metrics "
        "file.",
    )
    h3(doc, "6.3.5", "Estimation")
    para(
        doc,
        "The estimate was made bottom-up in lines of code and then converted to effort using a "
        "productivity assumption of about forty lines of debugged Python per hour, which is "
        "conservative for a student codebase with tests. The final system contains approximately "
        "3,200 lines: 1,900 in the vision and engine modules, 450 in the Flask application, 550 in "
        "the front end and 300 in scripts. At the assumed rate this corresponds to roughly eighty "
        "hours of coding; the actual effort was close to 210 hours, with the difference absorbed by "
        "dataset capture, tuning and documentation rather than by code volume. The estimate was "
        "therefore accurate for coding and badly low for the project as a whole, a familiar outcome "
        "in data-driven work.",
    )
    h3(doc, "6.3.6", "Risk Analysis")
    table_caption(doc, "6.6", "Risk register with mitigation and outcome")
    table(
        doc,
        ["Risk", "Likelihood", "Impact", "Mitigation", "Outcome"],
        [
            ("Lighting changes break the skin range", "High", "High",
             "Three presets plus fine tuning in the lab panel", "Reduced; still the main limitation"),
            ("Face merges with the hand contour", "High", "Medium",
             "Haar face detection subtracted from the mask", "Resolved"),
            ("Too few frames per class", "Medium", "High",
             "Capture target per sign and per-sign recall display", "Resolved; 160 to 400 per sign"),
            ("Over-fitting to one signer", "Medium", "High",
             "Six volunteers, varied distance and angle", "Partially mitigated"),
            ("Model file incompatible after a feature change", "Low", "High",
             "Feature version string checked on load", "Resolved"),
            ("Camera unavailable during demonstration", "Medium", "Medium",
             "Explicit error state and saved frames", "Resolved"),
            ("Scope creep in the interface", "High", "Medium",
             "Freeze interface after increment four", "Contained"),
        ],
        widths=[4.2, 2.0, 1.8, 3.8, 2.8],
        align="left",
        font_size=8.5,
    )
    h3(doc, "6.3.7", "Security Plan")
    para(
        doc,
        "The application handles video of the user's hand and face, which is personal data even when "
        "it is not identifying. Three rules were adopted. First, no frame is transmitted anywhere: "
        "the server binds to the loopback address, and the browser is on the same machine. Second, no "
        "image is written to disk unless the user presses Save frame, and captured training masks "
        "contain only the hand silhouette. Third, the reset action is the only destructive operation "
        "and requires an explicit confirmation, so a stray click cannot delete a dataset. The Flask "
        "server runs in development mode for the demonstration; a deployment would add a production "
        "WSGI server and an authentication layer before exposing it beyond localhost.",
    )
    h3(doc, "6.3.8", "Configuration Management Plan")
    para(
        doc,
        "The repository is organised by responsibility: src for the pipeline, templates and static "
        "for the interface, dataset for captured features and masks, models for the serialised "
        "bundle, and docs for the report and its generators. Configuration values that a user might "
        "reasonably change, such as the camera index, the region of interest, the smoothing window "
        "and the skin presets, live in a single module rather than being scattered through the code. "
        "The feature contract carries a version string; the model bundle stores the same string, and "
        "a mismatch is reported to the user instead of being silently accepted. Report figures are "
        "regenerated by scripts from the saved metrics file, so a change in the model produces a "
        "consistent set of charts rather than a hand-edited mixture.",
    )

    # ------------------------------------------------------------------ 6.4
    h2(doc, "6.4", "Design")
    h3(doc, "6.4.1", "Design Concept")
    para(
        doc,
        "The design follows three principles. Separation of concerns keeps the vision code free of "
        "HTTP and the interface free of OpenCV. A single source of truth for state means that the "
        "camera thread writes a snapshot structure under a lock and every reader sees a consistent "
        "view. Fail-visible contracts mean that the feature dimension and the feature version are "
        "asserted at the boundaries, so a mismatch surfaces as an error message rather than as a "
        "quietly wrong prediction.",
    )
    h3(doc, "6.4.2", "Design Technique")
    para(
        doc,
        "The design is object-oriented where state and lifetime matter and functional where a pure "
        "transformation is needed. Segmentation, feature extraction and classification are pure "
        "functions over arrays; the engine, the dataset and the model bundle are objects with "
        "explicit lifecycles. The interface is a thin client that renders a JSON snapshot and posts "
        "commands, which keeps the browser replaceable and the server testable without a display.",
    )
    h3(doc, "6.4.3", "Modelling")

    h3(doc, "6.4.3.1", "Detailed Class Diagram")
    para(
        doc,
        "Figure 6.6 shows the principal classes. The engine owns the model bundle and the transcript; "
        "segmentation and feature extraction are collaborators rather than subclasses, which allows "
        "the laboratory panel to run them on a stored image without starting a camera.",
    )
    figure(doc, D.fig("6.6"), "6.6",
           "Detailed class diagram of the application", width_cm=13.8)

    h3(doc, "6.4.3.2", "Interaction Diagram")
    h3(doc, "6.4.3.2.1", "Sequence Diagram")
    para(
        doc,
        "The design-level sequence in Figure 6.7 covers capture, training and reset, which are the "
        "three operations that change persistent state. The capture loop appends one row per accepted "
        "frame; training reads every row, evaluates on a held-out split and refits on the full set "
        "before saving.",
    )
    figure(doc, D.fig("6.7"), "6.7",
           "Sequence diagram for capture, training and reset", width_cm=14.0)

    h3(doc, "6.4.3.2.2", "Collaboration Diagram")
    para(
        doc,
        "Figure 6.8 presents the same objects as a collaboration diagram, with numbered messages. It "
        "is included because it makes the data flow easier to follow than the sequence diagram: the "
        "engine sits between the web layer and the vision layer, and the dataset is written by the "
        "engine rather than by the browser.",
    )
    figure(doc, D.fig("6.8"), "6.8",
           "Collaboration diagram of the main objects and their numbered messages", width_cm=13.6)

    h3(doc, "6.4.3.3", "State Diagram")
    para(
        doc,
        "The workbench is a state machine with a small number of stable states. Figure 6.9 shows "
        "them, including the two error paths that matter in practice: the camera failing to open and "
        "the model file being incompatible. The collecting and training states are entered from the "
        "laboratory panel and return to streaming when they finish.",
    )
    figure(doc, D.fig("6.9"), "6.9",
           "State diagram of the workbench, including camera-failure and training paths", width_cm=13.4)

    h3(doc, "6.4.3.4", "Activity Diagram")
    para(
        doc,
        "Figure 6.10 is the design-level activity diagram for the laboratory workflow. It differs "
        "from the conceptual activity diagram in Figure 6.3 because it includes the capture decision, "
        "the frame-acceptance test, the target count and the retraining step.",
    )
    figure(doc, D.fig("6.10"), "6.10",
           "Activity diagram of the capture and training workflow", width_cm=10.4)

    h3(doc, "6.4.3.5", "Object Diagram")
    para(
        doc,
        "Figure 6.11 is a snapshot of the object graph during a live run, with the values that were "
        "visible at the time. It is useful for two reasons: it documents the shape of the runtime "
        "data, and it shows the numbers that the interface displays, so a reader can connect the "
        "diagram to the screenshots in Section 6.5.",
    )
    figure(doc, D.fig("6.11"), "6.11",
           "Object diagram showing a live snapshot of the runtime objects", width_cm=13.8)

    h3(doc, "6.4.3.6", "Deployment Diagram")
    para(
        doc,
        "The deployment is deliberately local. Figure 6.12 shows the three nodes: the browser, the "
        "host process that serves HTTP and runs the vision thread, and the camera. No cloud node "
        "exists, which is both a privacy property and a reason the system works offline.",
    )
    figure(doc, D.fig("6.12"), "6.12",
           "Deployment diagram: browser, host process and camera", width_cm=13.8)

    h3(doc, "6.4.3.7", "Component Diagram")
    para(
        doc,
        "Figure 6.13 groups the source files into four components. The boundaries correspond to "
        "directories in the repository, which keeps the diagram honest: a component that grows a "
        "dependency is visible as an import that crosses a directory.",
    )
    figure(doc, D.fig("6.13"), "6.13",
           "Component diagram of the repository", width_cm=13.8)

    # ------------------------------------------------------------------ 6.5
    h2(doc, "6.5", "Implementation Phase")
    h3(doc, "6.5.1", "Language Used Characteristics")
    para(
        doc,
        "Python's strengths for this project are library coverage and readability. OpenCV's Python "
        "bindings expose the full C++ API, so the contour operations run at native speed while the "
        "surrounding logic stays legible. NumPy provides vectorised arithmetic without a compilation "
        "step. The weaknesses are equally relevant: the global interpreter lock means that a "
        "CPU-bound loop competes with the web server, which is why the vision loop runs in its own "
        "thread and publishes snapshots rather than being called from request handlers. Python's "
        "dynamic typing is offset by dataclasses for the segmentation result and the feature bundle, "
        "and by assertions at the boundaries where a wrong shape would be expensive.",
    )
    para(
        doc,
        "JavaScript is used only for rendering and for posting commands. It is deliberately plain: "
        "one file, no framework, no build step. The browser's speech synthesis API provides the "
        "speak function without any server-side dependency.",
    )

    h3(doc, "6.5.2", "Coding")
    para(
        doc,
        "The desk is the first screen the user sees. Figure 6.14 shows the complete page: the header "
        "with the camera status, the live stage with the region-of-interest brackets and the overlay, "
        "the four readouts for motion, frame rate, hand presence and shape, and the reading and "
        "transcript panels below.",
    )
    figure(doc, D.fig("6.14"), "6.14",
           "Desk view of the workbench, showing the live stage and the readout strip", width_cm=11.6)
    para(
        doc,
        "The screenshot was taken with no hand in the scan box, which is why the stage reads "
        "SEARCHING and the reading panel asks for a hand. The state is deliberate in this figure: it "
        "shows the system's empty state, including the model line that reports 97.7 per cent "
        "held-out accuracy and 6,983 frames.",
    )
    figure(doc, D.fig("6.15"), "6.15",
           "Reading panel, transcript, action buttons and the model summary", width_cm=13.4)
    para(
        doc,
        "Figure 6.15 shows the lower half of the desk. The reading panel is dark so that the letter "
        "dominates; the confidence bar and the hold bar are separate because they answer different "
        "questions. The transcript behaves like a text field, with space, delete and clear available "
        "both as buttons and as keyboard shortcuts.",
    )
    figure(doc, D.fig("6.16"), "6.16",
           "Laboratory panel: skin range presets and the four segmentation stages", width_cm=13.2)
    para(
        doc,
        "The laboratory panel in Figure 6.16 is the part of the interface that makes the project "
        "teachable. The three presets change the HSV bounds immediately, and the four stage images "
        "show the contour, the equalised luminance, the skin mask and the warped shape. The stage "
        "images are produced by the same segmentation code that runs live, not by a separate "
        "demonstration path.",
    )
    figure(doc, D.fig("6.17"), "6.17",
           "Sign library with frame count and held-out recall for each of the twenty-six signs",
           width_cm=13.2)
    para(
        doc,
        "Figure 6.17 is the sign library. Each tile reports the number of stored frames and the "
        "held-out recall for that sign, with a bar for quick comparison. This view was added because "
        "a single overall accuracy hides the letters that actually fail, and because it lets the user "
        "see immediately which sign needs more frames.",
    )
    figure(doc, D.fig("6.18"), "6.18",
           "Training controls: label, frame target, capture, stop, train and reset", width_cm=13.2)
    para(
        doc,
        "Figure 6.18 shows the training controls. The label field accepts one to three characters, "
        "the frame target defaults to eighty, and the status line reports the total frames and the "
        "model's held-out accuracy. Reset is separated from train and requires confirmation, because "
        "it deletes both the captures and the model.",
    )

    h3(doc, "6.5.3", "Code Efficiency")
    para(
        doc,
        "Table 6.7 lists the measured cost of each stage on the development laptop. The figures are "
        "averages over 300 frames of a recorded session, measured inside the engine loop with a "
        "monotonic clock.",
    )
    table_caption(doc, "6.7", "Measured cost per frame by stage")
    table(
        doc,
        ["Stage", "Mean time (ms)", "Share of frame budget"],
        [
            ("Colour conversion and CLAHE", "3.1", "9%"),
            ("HSV threshold and morphology", "2.4", "7%"),
            ("Face detection (Haar)", "4.8", "14%"),
            ("Contour, hull and defects", "1.7", "5%"),
            ("Feature extraction (61-D)", "0.9", "3%"),
            ("SVC prediction with probability", "0.8", "2%"),
            ("Overlay drawing and JPEG encoding", "6.2", "19%"),
            ("Remaining (capture, copy, scheduling)", "13.6", "41%"),
            ("Total per frame", "33.5", "100%"),
        ],
        widths=[7.4, 3.4, 3.6],
        align="left",
        first_col_bold=True,
    )
    para(
        doc,
        "The total of about 33.5 milliseconds corresponds to roughly thirty frames per second, which "
        "matches the 29.5 frames per second reported by the interface. The largest single cost is "
        "encoding, not recognition: the classifier accounts for less than one millisecond, which is "
        "the practical argument for the classical approach on CPU-only hardware.",
    )

    h3(doc, "6.5.4", "Optimization of Code")
    para(doc, "Four optimisations were applied after profiling.")
    bullets(
        doc,
        [
            ("Face detection throttling. ", "The cascade runs on every third frame and the last box "
             "is reused in between. This removed about three milliseconds per frame with no visible "
             "change in behaviour."),
            ("Region of interest. ", "Thresholding and morphology operate on the right half of the "
             "frame rather than the whole image, which halves the pixel count of the most frequent "
             "operations."),
            ("Single resampling. ", "The contour is resampled once and reused by the Fourier and "
             "radial blocks instead of being resampled twice."),
            ("Snapshot instead of shared arrays. ", "The camera thread publishes an immutable "
             "snapshot, so request handlers never copy a frame and never block the loop."),
        ],
    )

    h3(doc, "6.5.5", "Validation Check")
    para(
        doc,
        "Validation is performed at three boundaries. The feature vector is checked against "
        "FEATURE_DIM and rejected if it differs. The model bundle stores the feature version and the "
        "application refuses to use a bundle whose version does not match. The dataset loader checks "
        "that every row has the expected width before fitting, so a corrupted capture file produces "
        "a clear error rather than a shape mismatch deep inside scikit-learn. In addition, the "
        "training routine enforces minimum class and sample counts and refuses to fit a model that "
        "cannot be evaluated on a stratified split.",
    )

    # ------------------------------------------------------------------ 6.6
    h2(doc, "6.6", "Testing")
    h3(doc, "6.6.1", "Testing Objectives")
    para(
        doc,
        "Testing had four objectives: to confirm that each functional requirement is met, to measure "
        "recognition accuracy on data the model has not seen, to find the conditions under which the "
        "system fails, and to check that failures are reported rather than hidden. The last objective "
        "is as important as the first, because a recognition system that silently returns a wrong "
        "letter is worse than one that says it cannot see a hand.",
    )

    h3(doc, "6.6.2", "Testing Methods & Strategies used along with test data")
    para(
        doc,
        "Three strategies were combined. Unit-level checks were used for the pure functions: "
        "resampling a known contour, verifying that a feature vector has sixty-one finite values, "
        "and confirming that a bundle with the wrong version is rejected. Functional tests were "
        "executed through the browser against the requirements in Table 6.1. Statistical testing was "
        "performed by the training routine itself, which holds out a stratified quarter of the "
        "frames and reports accuracy, per-class precision, recall and F1, and the confusion matrix.",
    )
    para(
        doc,
        f"The statistical test data are the captured frames: {D.SAMPLES:,} frames across "
        f"{len(D.LABELS)} classes, split into a training set and a held-out set of "
        f"{D.TEST_SAMPLES:,} frames. The split is stratified and seeded, so the reported number is "
        "reproducible. Frames from the same capture session can appear on both sides of the split, "
        "which makes the result an upper bound on signer-independent performance; this is discussed "
        "in Section 7.1.",
    )
    table_caption(doc, "6.8", "Functional test cases and results")
    table(
        doc,
        ["ID", "Test", "Expected result", "Actual result", "Status"],
        [
            ("T1", "Open the page with the camera connected", "Live stage streams within two seconds", "Streams at about 29.5 fps", "Pass"),
            ("T2", "Hold a letter inside the box", "Reading shows the letter and a confidence", "Letter and bar update per frame", "Pass"),
            ("T3", "Hold the same letter for three seconds", "Exactly one letter is committed", "One commit, then suppression", "Pass"),
            ("T4", "Remove the hand", "Reading returns to the empty state", "Panel shows waiting for hand", "Pass"),
            ("T5", "Switch skin preset", "Mask updates without restart", "Mask changes immediately", "Pass"),
            ("T6", "Capture 40 frames of a new label", "Counter reaches 40 and stops", "Counter stops at target", "Pass"),
            ("T7", "Train with all 26 labels", "Report and reload", "97.71% held-out, model reloaded", "Pass"),
            ("T8", "Reset with confirmation", "Dataset and model removed", "Files removed, desk reverts", "Pass"),
            ("T9", "Unplug the camera during a run", "Error state, no crash", "Camera error shown, server alive", "Pass"),
            ("T10", "Load a model with an old feature version", "Clear rejection message", "Version error reported", "Pass"),
        ],
        widths=[1.2, 4.4, 4.2, 3.4, 1.4],
        align="left",
        font_size=8.5,
    )

    h3(doc, "6.6.3", "Test results and analysis")
    table_caption(doc, "6.9", "Summary of held-out evaluation")
    table(
        doc,
        ["Metric", "Value"],
        [
            ("Classes", f"{len(D.LABELS)} (A to Z)"),
            ("Total frames", f"{D.SAMPLES:,}"),
            ("Held-out frames", f"{D.TEST_SAMPLES:,} (25%, stratified)"),
            ("Training accuracy", D.pct(D.TRAIN_ACCURACY)),
            ("Held-out accuracy", D.pct(D.ACCURACY)),
            ("Macro F1", f"{D.MACRO_F1:.4f}"),
            ("Weighted F1", f"{D.WEIGHTED_F1:.4f}"),
            ("Frames per class", "160 to 400 (mean 269)"),
        ],
        widths=[5.6, 8.8],
        align="left",
        first_col_bold=True,
    )
    para(
        doc,
        f"The model reaches {D.pct(D.ACCURACY)} on the held-out split, with a macro F1 of "
        f"{D.MACRO_F1:.4f}. The difference between macro and weighted F1 is small, which indicates "
        "that the classes are reasonably balanced and that the larger classes are not carrying the "
        "score.",
    )
    graph(doc, D.graph_path("6.1"), "6.1",
          "Number of captured frames for each sign, with the mean marked", width_cm=11.6)
    para(
        doc,
        "Graph 6.1 shows the capture counts. The dataset is not perfectly balanced: A has 252 frames "
        "and C and D have 160 each, while O has 400. The imbalance is modest and is partly corrected "
        "by the balanced class weight in the classifier.",
    )
    graph(doc, D.graph_path("6.2"), "6.2",
          "Held-out recall for each sign, sorted from weakest to strongest", width_cm=11.6)
    para(
        doc,
        "Graph 6.2 is the most informative single view of the model. Most signs are above ninety "
        "per cent, but B, C and D sit at the bottom. These are the letters formed with a closed or "
        "partly closed hand, where the silhouette is a compact blob and the differences between "
        "letters lie in the position of the thumb rather than in the outline. The descriptor sees the "
        "outline well and the interior poorly, which is exactly the limitation predicted in Section "
        "5.5.",
    )
    graph(doc, D.graph_path("6.3"), "6.3",
          "Confusion matrix on the held-out split, normalised by true class", width_cm=12.4)
    para(
        doc,
        "The confusion matrix in Graph 6.3 confirms the reading of Graph 6.2. Off-diagonal mass is "
        "concentrated between visually similar closed-hand letters and between letters that differ "
        "by a single extended finger. The matrix is close to diagonal, which means that errors are "
        "confusions between neighbours rather than random failures.",
    )
    graph(doc, D.graph_path("6.4"), "6.4",
          "Training accuracy against held-out accuracy, and the distribution of per-sign F1",
          width_cm=12.6)
    para(
        doc,
        "Graph 6.4(a) compares the fit on the training data with the held-out result. A training "
        "accuracy of 99.92 per cent against 97.71 per cent held-out is a gap of about two percentage "
        "points, which is consistent with a model that has enough capacity for the classes but is not "
        "memorising individual frames. Graph 6.4(b) shows that most signs have an F1 above ninety-six "
        "per cent, with a short tail of weaker classes.",
    )
    graph(doc, D.graph_path("6.5"), "6.5",
          "Relationship between the number of frames captured for a sign and its held-out recall",
          width_cm=10.8)
    para(
        doc,
        "Graph 6.5 tests the obvious hypothesis that more frames produce better recall. The "
        "correlation is weak, and the fitted line is almost flat. Capture count is therefore not the "
        "explanation for the weak classes; the difficulty of the shape is. This is a useful negative "
        "result, because it argues against simply recording more frames of B, C and D and expecting "
        "the problem to disappear.",
    )
    table_caption(doc, "6.10", "Strongest and weakest signs on the held-out split")
    ranked = sorted(D.LABELS, key=lambda l: D.PER_CLASS[l]["recall"], reverse=True)
    rows = []
    for label in ranked[:4]:
        m = D.PER_CLASS[label]
        rows.append((label, f"{m['recall'] * 100:.1f}%", f"{m['precision'] * 100:.1f}%",
                     f"{m['f1'] * 100:.1f}%", str(m["support"])))
    rows.append(("\u2026", "\u2026", "\u2026", "\u2026", "\u2026"))
    for label in ranked[-4:]:
        m = D.PER_CLASS[label]
        rows.append((label, f"{m['recall'] * 100:.1f}%", f"{m['precision'] * 100:.1f}%",
                     f"{m['f1'] * 100:.1f}%", str(m["support"])))
    table(
        doc,
        ["Sign", "Recall", "Precision", "F1", "Support"],
        rows,
        widths=[3.0, 3.0, 3.0, 3.0, 2.4],
        align="center",
        first_col_bold=True,
    )
    para(
        doc,
        "Table 6.10 lists the extremes. The full per-sign table is given in Annexure I so that the "
        "body of the report stays readable. The weakest classes are not the rarest ones, which "
        "supports the conclusion that shape ambiguity, not data scarcity, is the limiting factor.",
    )
