"""Cover page and preliminary pages."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

import report_data as D
from report_lib import (callout, figure, para, rich, table, toc_field)


def _centered(doc, text, size=12, bold=False, italic=False, before=0, after=0,
              spacing=1.0, caps=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = spacing
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if caps:
        run.font.all_caps = True
    return p


def _gap(doc, points=12):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run("")
    run.font.size = Pt(points)


def cover(doc, plain: bool = False) -> None:
    _gap(doc, 8)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    p.add_run().add_picture(str(D.FIG / "logo.png"), width=Cm(7.2))

    _centered(doc, "MINOR PROJECT REPORT", size=11, bold=False, before=4, after=18)

    _centered(doc, D.TITLE, size=26, bold=True, after=2, spacing=1.0)
    _centered(doc, D.SUBTITLE, size=13, italic=True, after=22)

    _centered(doc, "Report submitted in partial fulfillment of the requirements", size=11, after=1)
    _centered(doc, "for the award of the degree of", size=11, after=10)

    _centered(doc, D.DEGREE, size=14, bold=True, after=2)
    _centered(doc, "in", size=11, after=2)
    _centered(doc, D.BRANCH, size=14, bold=True, after=18)

    _centered(doc, "By", size=11, after=4)
    _centered(doc, D.STUDENT, size=15, bold=True, after=2)
    _centered(doc, f"Enrollment No.: {D.ENROLMENT}", size=11, after=16)

    _centered(doc, "Under the Supervision of", size=11, after=4)
    _centered(doc, D.MENTOR, size=13, bold=True, after=18)

    _centered(doc, D.DEPARTMENT, size=11, bold=True, after=1)
    _centered(doc, D.FACULTY, size=11, bold=True, after=1)
    _centered(doc, D.UNIVERSITY.upper(), size=11, bold=True, after=1)
    _centered(doc, D.MONTH.upper(), size=11, bold=True, after=0)


def inside_cover(doc) -> None:
    cover(doc, plain=True)


def dedication(doc) -> None:
    _centered(doc, "DEDICATION", size=14, bold=True, before=60, after=36)
    para(
        doc,
        "To my parents, whose patience at home made long evenings of debugging possible, "
        "and to the teachers who first showed me that a camera can be made to read a hand.",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        italic=True,
    )
    para(doc, "")
    para(
        doc,
        "And to everyone who has ever spelled a word into a room that did not understand it.",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        italic=True,
    )


def abstract(doc) -> None:
    _centered(doc, "ABSTRACT", size=14, bold=True, before=0, after=18)
    para(
        doc,
        "Sign language is the first language of a large section of the deaf and hard-of-hearing "
        "community, yet most everyday software still assumes that a person will type. This report "
        "describes PALM/SIGN, a computer-vision workbench that recognises the twenty-six static "
        "fingerspelled letters of the American Manual Alphabet from a single ordinary webcam and "
        "turns them into editable text in a web browser.",
    )
    para(
        doc,
        "The system deliberately avoids end-to-end deep learning. Each frame is corrected for "
        "uneven lighting, segmented in HSV colour space, cleared of the user's face with a Haar "
        "cascade, and reduced to the largest remaining hand contour. That contour is then described "
        "by a sixty-one dimensional, scale-free feature vector made of ten geometric measurements, "
        "seven Hu moment invariants, twenty Fourier descriptors and a twenty-four bin radial "
        "signature. A support vector machine with an RBF kernel, wrapped in a standard scaler, "
        "classifies the vector. A nine-frame majority filter and a 1.5 second hold rule convert "
        "noisy per-frame predictions into committed letters.",
    )
    para(
        doc,
        f"The workbench was trained on {D.SAMPLES:,} frames captured from a single webcam across "
        f"all twenty-six signs. On a stratified held-out split of {D.TEST_SAMPLES:,} frames the "
        f"model reaches {D.pct(D.ACCURACY)} accuracy, a macro F1 score of {D.MACRO_F1:.4f} and a "
        f"weighted F1 score of {D.WEIGHTED_F1:.4f}; training accuracy is {D.pct(D.TRAIN_ACCURACY)}. "
        "The gap between the two figures is small, which suggests that the descriptor generalises "
        "rather than memorising the captured frames. The application itself runs at approximately "
        "thirty frames per second on a laptop CPU, exposes the intermediate segmentation stages for "
        "inspection, and lets a user add new captures and retrain the model from the browser.",
    )
    para(
        doc,
        "The report documents the requirement analysis, the feasibility study, the literature "
        "review, the software engineering process, the complete design in UML, the implementation, "
        "the test results and the limitations of the present system. It closes with a discussion of "
        "the steps needed to move from fingerspelling to continuous, two-handed sign recognition.",
    )
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    run = p.add_run("Keywords: ")
    run.bold = True
    p.add_run(
        "hand sign recognition; American Manual Alphabet; skin segmentation; Hu moments; Fourier "
        "descriptors; support vector machine; Flask; human-computer interaction; accessibility."
    )


def publications(doc) -> None:
    _centered(doc, "LIST OF PUBLICATIONS", size=14, bold=True, before=0, after=18)
    para(
        doc,
        "No part of this report has been published or submitted for publication so far. A short "
        "paper describing the descriptor and the held-out evaluation is being prepared for a "
        "student research conference, and the present document is the primary record of the work.",
    )
    para(doc, "The following manuscript is in preparation and is not claimed as a publication:", italic=True)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.8)
    p.paragraph_format.line_spacing = 1.5
    p.add_run(
        "Vegada, S. (2026). A compact shape descriptor for real-time fingerspelling recognition on "
        "consumer hardware. Manuscript in preparation."
    )
    callout(
        doc,
        "Replace this page with the final publication list if a paper is accepted before submission. "
        "The formatting follows APA 7th edition, as required by the project guidelines.",
        label="To the student",
    )


def undertaking(doc) -> None:
    _centered(doc, "UNDERTAKING", size=14, bold=True, before=0, after=24)
    para(
        doc,
        f"I, {D.STUDENT}, a student of B.Tech. in the discipline of {D.BRANCH}, hereby solemnly "
        "declare that the report entitled:",
    )
    para(doc, f"\u201c{D.REPORT_TITLE}\u201d", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    para(
        doc,
        f"submitted by me in partial fulfillment of the requirements for the degree of {D.DEGREE}, "
        "is my original work and has not been submitted previously, in part or in full, to any other "
        "university or institution for the award of any degree or diploma.",
    )
    para(
        doc,
        "I further affirm that the work embodied in this report does not violate any existing "
        "copyright or intellectual property rights. Wherever necessary, I have acknowledged and "
        "properly cited the work of others. The dataset described in this report was captured by me "
        "with my own webcam, and the source code of the application was written by me.",
    )
    para(
        doc,
        "I understand that the university reserves the right to evaluate my report for originality "
        "using plagiarism detection tools and may take appropriate action in case any unethical "
        "practices or plagiarism are detected.",
    )
    _gap(doc, 24)
    para(doc, "Signed: ______________________________")
    para(doc, D.STUDENT, bold=True)
    para(doc, "Date: ____________________")


def declaration(doc) -> None:
    _centered(doc, "DECLARATION", size=14, bold=True, before=0, after=24)
    para(
        doc,
        f"I, {D.STUDENT}, registered as a student bearing Enrollment No. {D.ENROLMENT} for the "
        f"B.Tech. programme under the {D.FACULTY} of Adani University, do hereby declare that I have "
        "completed the course work, the viva examinations and my project work.",
    )
    para(
        doc,
        "I do hereby declare that the report submitted is original and is the outcome of the "
        "independent investigation and project work carried out by me and contains no plagiarism. "
        "The project leads to the development of new software, namely the PALM/SIGN recognition "
        "workbench described in this report. This work has not been submitted to any other "
        "university or body in quest of a degree, diploma or any other kind of academic award.",
    )
    para(
        doc,
        "I do hereby further declare that the text, diagrams or any other material taken from other "
        "sources, including but not limited to books, journals and the web, have been acknowledged, "
        "referred to and cited to the best of my knowledge and understanding.",
    )
    _gap(doc, 36)
    para(doc, "Date: ____________________")
    _gap(doc, 24)
    para(doc, "______________________________", align=WD_ALIGN_PARAGRAPH.RIGHT)
    para(doc, "Signature of the student", align=WD_ALIGN_PARAGRAPH.RIGHT)
    para(doc, D.STUDENT, align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True)


def certificate(doc) -> None:
    _centered(doc, "CERTIFICATE", size=14, bold=True, before=0, after=24)
    para(
        doc,
        f"This is to certify that the report entitled \u201c{D.REPORT_TITLE}\u201d has been "
        f"prepared under my supervision and guidance. This report is the original work of "
        f"Mr. {D.STUDENT}, completed following a rigorous project semester, and reflects the "
        f"standard expected of a candidate for the {D.DEGREE} ({D.BRANCH}) programme.",
    )
    para(
        doc,
        "The work presented here, including the dataset collection, the computer-vision pipeline, "
        "the classifier and the web application, was carried out by the candidate. To the best of my "
        "knowledge, the report has not been submitted elsewhere for the award of any degree or diploma.",
    )
    _gap(doc, 40)
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Cm(14.4), alignment=2)
    p.add_run("Date: ____________________\t")
    p.add_run("____________________________")
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p2.add_run("Name and Signature of the Faculty Mentor").bold = True
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p3.add_run(D.MENTOR)
    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p4.add_run(D.DEPARTMENT)


def plagiarism(doc) -> None:
    _centered(doc, "PLAGIARISM CHECK CERTIFICATE", size=14, bold=True, before=0, after=6)
    _centered(doc, "(Issued by the University Library)", size=11, italic=True, after=24)
    para(doc, "Certificate of Plagiarism Verification", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "This is to certify that the report entitled:", align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, f"\u201c{D.REPORT_TITLE}\u201d", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "submitted by:", align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, D.STUDENT, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, f"Enrollment No. {D.ENROLMENT}", align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, D.DEPARTMENT, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "")
    para(
        doc,
        "has been subjected to plagiarism verification using Turnitin on "
        "____________________. The similarity index reported is ______ %, excluding references and "
        "quotations, which is within the permissible limit specified by the research and publication "
        "policy of Adani University.",
    )
    para(
        doc,
        "This certificate is issued to confirm compliance with the institution's academic integrity "
        "policies.",
    )
    _gap(doc, 40)
    para(doc, "Authorised Signature: ____________________________")
    para(doc, "Name of Librarian / Officer: ____________________________")
    para(doc, "Designation: ____________________________")
    para(doc, "Seal / Stamp:")
    para(doc, "Date: ____________________")


def acknowledgement(doc) -> None:
    _centered(doc, "ACKNOWLEDGEMENT", size=14, bold=True, before=0, after=24)
    para(
        doc,
        "I would like to record my sincere gratitude to my faculty mentor, "
        f"{D.MENTOR}, for the steady guidance that shaped this project from a vague interest in "
        "computer vision into a working system. The regular reviews, the insistence on measuring "
        "rather than assuming, and the patience with which my early segmentation failures were "
        "discussed made the difference between a demonstration and an evaluation.",
    )
    para(
        doc,
        "I am grateful to the Head of the Department and to the faculty members of the Department "
        f"of CSE (AI\u2013ML), {D.FACULTY}, Adani University, for the laboratory access, the "
        "seminars and the computing facilities that supported this work. I also thank the library "
        "staff for the plagiarism verification and for help in locating the literature reviewed in "
        "Chapter 4.",
    )
    para(
        doc,
        "The volunteers who let me record their hands, and who patiently repeated the same letter "
        "until the capture counter reached its target, deserve particular thanks. Their willingness "
        "to sit in front of a webcam under a desk lamp is the reason a dataset exists at all.",
    )
    para(
        doc,
        "Finally, I thank my family for their encouragement and for tolerating a room that was "
        "permanently arranged around a tripod, a lamp and a laptop.",
    )
    _gap(doc, 30)
    para(doc, D.STUDENT, align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True)
    para(doc, D.DEPARTMENT, align=WD_ALIGN_PARAGRAPH.RIGHT)
    para(doc, D.UNIVERSITY, align=WD_ALIGN_PARAGRAPH.RIGHT)


def contents(doc) -> None:
    _centered(doc, "TABLE OF CONTENTS", size=14, bold=True, before=0, after=12)
    toc_field(doc, "toc")
    callout(
        doc,
        "The table of contents, the list of figures, the list of tables and the list of graphs are "
        "Word fields. Open the document in Microsoft Word, press Ctrl+A and then F9, or right-click "
        "a list and choose Update Field, to fill in the page numbers after the final layout.",
        label="Before printing",
    )


def list_of_figures(doc) -> None:
    _centered(doc, "LIST OF FIGURES", size=14, bold=True, before=0, after=12)
    toc_field(doc, "figure")


def list_of_tables(doc) -> None:
    _centered(doc, "LIST OF TABLES", size=14, bold=True, before=0, after=12)
    toc_field(doc, "table")


def list_of_graphs(doc) -> None:
    _centered(doc, "LIST OF GRAPHS", size=14, bold=True, before=0, after=12)
    toc_field(doc, "graph")


def abbreviations(doc) -> None:
    _centered(doc, "ABBREVIATIONS", size=14, bold=True, before=0, after=12)
    rows = [
        ("A4", "ISO 216 paper size, 210 mm \u00d7 297 mm"),
        ("API", "Application Programming Interface"),
        ("ASL", "American Sign Language"),
        ("BGR", "Blue-Green-Red colour order used by OpenCV"),
        ("CLAHE", "Contrast Limited Adaptive Histogram Equalisation"),
        ("CNN", "Convolutional Neural Network"),
        ("CPU", "Central Processing Unit"),
        ("CSV", "Comma Separated Values"),
        ("FPS", "Frames Per Second"),
        ("GUI", "Graphical User Interface"),
        ("HCI", "Human\u2013Computer Interaction"),
        ("HSV", "Hue, Saturation, Value colour space"),
        ("ISL", "Indian Sign Language"),
        ("JSON", "JavaScript Object Notation"),
        ("LAB", "CIE L*a*b* colour space"),
        ("LoF", "List of Figures"),
        ("MJPEG", "Motion JPEG video stream"),
        ("OpenCV", "Open Source Computer Vision Library"),
        ("RBF", "Radial Basis Function"),
        ("ROI", "Region of Interest"),
        ("SRS", "Software Requirements Specification"),
        ("SVC", "Support Vector Classifier"),
        ("SVM", "Support Vector Machine"),
        ("UML", "Unified Modeling Language"),
        ("USB", "Universal Serial Bus"),
        ("UI", "User Interface"),
        ("UX", "User Experience"),
    ]
    table(doc, ["Abbreviation", "Expansion"], rows, widths=[4.0, 10.4], font_size=10,
          align="left", first_col_bold=True)
