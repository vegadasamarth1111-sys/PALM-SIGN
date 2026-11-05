"""Build the PALM/SIGN minor project report as a Word document."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.shared import Pt  # noqa: E402

import content_ch1_4 as C14  # noqa: E402
import content_ch5 as C5  # noqa: E402
import content_ch6 as C6  # noqa: E402
import content_ch7_8 as C78  # noqa: E402
import content_front as CF  # noqa: E402
import report_data as D  # noqa: E402
from report_lib import (collapse_page_breaks, enable_update_fields,  # noqa: E402
                        new_document, page_break, start_section,
                        suppress_footer)


def build(out: Path) -> Path:
    doc = new_document()

    # ---------------------------------------------------------- cover (unnumbered)
    CF.cover(doc)
    suppress_footer(doc.sections[0])
    page_break(doc)
    CF.inside_cover(doc)

    # ---------------------------------------------------------- preliminaries (i..)
    start_section(doc, "lowerRoman", 1)
    CF.dedication(doc)
    page_break(doc)
    CF.abstract(doc)
    page_break(doc)
    CF.publications(doc)
    page_break(doc)
    CF.undertaking(doc)
    page_break(doc)
    CF.declaration(doc)
    page_break(doc)
    CF.certificate(doc)
    page_break(doc)
    CF.plagiarism(doc)
    page_break(doc)
    CF.acknowledgement(doc)
    page_break(doc)
    CF.contents(doc)
    page_break(doc)
    CF.list_of_figures(doc)
    page_break(doc)
    CF.list_of_tables(doc)
    page_break(doc)
    CF.list_of_graphs(doc)
    page_break(doc)
    CF.abbreviations(doc)

    # ---------------------------------------------------------- chapters (1..)
    start_section(doc, "decimal", 1)
    C14.chapter1(doc)
    page_break(doc)
    C14.chapter2(doc)
    page_break(doc)
    C14.chapter3(doc)
    page_break(doc)
    C14.chapter4(doc)
    page_break(doc)
    C5.chapter5(doc)
    page_break(doc)
    C6.chapter6(doc)
    page_break(doc)
    C78.chapter7(doc)
    page_break(doc)
    C78.chapter8(doc)
    page_break(doc)
    C78.annexure1(doc)
    page_break(doc)
    C78.annexure2(doc)

    enable_update_fields(doc)
    collapse_page_breaks(doc)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return out


if __name__ == "__main__":
    target = D.ROOT / "PALM_SIGN_Minor_Project_Report.docx"
    path = build(target)
    print("wrote", path, path.stat().st_size, "bytes")
