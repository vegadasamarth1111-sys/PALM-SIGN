"""Refresh the report fields in Word, restyle the lists, and export a PDF.

Word rebuilds the contents fields on every update and stamps its own bold
``TOC 1`` style onto the figure, table and graph lists. Restyling those
paragraphs through the object model forces a full repagination for every
paragraph and is very slow, so the style is swapped in the saved XML instead
and a second, short Word session exports the PDF.
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

import win32com.client as win32

DOCX = Path(__file__).resolve().parent / "PALM_SIGN_Minor_Project_Report.docx"
PDF = DOCX.with_suffix(".pdf")

WD_STATISTIC_PAGES = 2
WD_FORMAT_PDF = 17
WD_STYLE_PARAGRAPH = 1

CAPTION_START = re.compile(r"<w:t[^>]*>(?:Figure|Table|Graph) \d")


def ensure_list_entry_style(doc) -> None:
    """Create the compact, non-bold style used by the three lists."""
    name = "List Entry"
    try:
        style = doc.Styles(name)
    except Exception:  # noqa: BLE001
        style = doc.Styles.Add(Name=name, Type=WD_STYLE_PARAGRAPH)
    style.Font.Name = "Times New Roman"
    style.Font.Size = 10.5
    style.Font.Bold = False
    style.ParagraphFormat.SpaceBefore = 0
    style.ParagraphFormat.SpaceAfter = 2
    style.ParagraphFormat.LineSpacingRule = 0  # single
    style.ParagraphFormat.LeftIndent = 0
    style.ParagraphFormat.FirstLineIndent = 0


def restyle_lists(path: Path) -> int:
    """Point every caption-list paragraph at the List Entry style.

    The tab stop with the dot leader is left untouched: only the paragraph
    style id is rewritten.
    """
    tmp = path.with_suffix(".tmp.docx")
    changed = 0
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/document.xml":
                xml = data.decode("utf-8")
                out = []
                for para in re.split(r"(?=<w:p\b)", xml):
                    if ('<w:pStyle w:val="TOC1"/>' in para
                            and CAPTION_START.search(para)
                            and para.count("<w:pStyle") == 1):
                        para = para.replace('<w:pStyle w:val="TOC1"/>',
                                            '<w:pStyle w:val="ListEntry"/>', 1)
                        changed += 1
                    out.append(para)
                data = "".join(out).encode("utf-8")
            dst.writestr(item, data)
    shutil.move(str(tmp), str(path))
    return changed


def main() -> int:
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        # ---- pass one: build the fields
        doc = word.Documents.Open(str(DOCX), ReadOnly=False, AddToRecentFiles=False)
        ensure_list_entry_style(doc)
        try:
            doc.Fields.Update()
        except Exception as exc:  # noqa: BLE001
            print("field update warning:", exc)
        for collection in ("TablesOfContents", "TablesOfFigures"):
            try:
                items = getattr(doc, collection)
                for i in range(1, items.Count + 1):
                    items(i).Update()
            except Exception as exc:  # noqa: BLE001
                print(f"{collection} warning:", exc)
        doc.Repaginate()
        doc.Save()
        doc.Close(False)

        # ---- python pass: swap the style id of the list entries
        changed = restyle_lists(DOCX)
        print(f"restyled {changed} list entries")

        # ---- pass two: export
        doc = word.Documents.Open(str(DOCX), ReadOnly=False, AddToRecentFiles=False)
        doc.Repaginate()
        pages = doc.ComputeStatistics(WD_STATISTIC_PAGES)
        words = doc.ComputeStatistics(0)
        doc.Save()
        doc.SaveAs2(str(PDF), FileFormat=WD_FORMAT_PDF)
        doc.Close(False)
        print(f"pages={pages} words={words}")
        print("pdf", PDF, PDF.stat().st_size, "bytes")
        return 0
    finally:
        word.Quit()


if __name__ == "__main__":
    sys.exit(main())
