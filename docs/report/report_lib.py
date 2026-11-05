"""Reusable python-docx helpers that follow the Adani University report guidelines."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

FONT = "Times New Roman"
INK = RGBColor(0x00, 0x00, 0x00)
MUTED = RGBColor(0x44, 0x44, 0x44)
ACCENT = RGBColor(0xC9, 0x40, 0x1F)

CONTENT_WIDTH_CM = 14.6


# --------------------------------------------------------------------- setup
def _set_cell_margins(cell, top=60, bottom=60, left=90, right=90) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def _borders(table, sz=6, color="7A7A7A") -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def _shade(cell, hexcolor: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def _cant_split(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trPr.append(el)


def _keep_rows_together(tbl) -> None:
    """Ask Word not to break a short table across two pages."""
    for row in tbl.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True


def _repeat_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _keep_with_next(paragraph, on: bool = True) -> None:
    paragraph.paragraph_format.keep_with_next = on


def field(paragraph, instruction: str, placeholder: str = "") -> None:
    """Insert a Word field (PAGE, TOC, ...) into a paragraph."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    run._r.append(begin)

    run = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    run._r.append(instr)

    run = paragraph.add_run()
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    run._r.append(sep)

    if placeholder:
        paragraph.add_run(placeholder)

    run = paragraph.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)


def new_document() -> Document:
    doc = Document()

    # A4
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(12)
    normal.font.color.rgb = INK
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    _configure_heading(doc, "Heading 1", 14, centered=True, caps=True, before=0, after=18)
    _configure_heading(doc, "Heading 2", 12, centered=False, caps=False, before=16, after=8)
    _configure_heading(doc, "Heading 3", 12, centered=False, caps=False, before=12, after=6, italic=False)

    _make_style(doc, "Figure Caption", 10.5, centered=True, before=4, after=12, spacing=1.0)
    _make_style(doc, "Table Caption", 10.5, centered=True, before=12, after=4, spacing=1.0)
    _make_style(doc, "Graph Caption", 10.5, centered=True, before=4, after=12, spacing=1.0)
    _make_style(doc, "Front Matter", 12, centered=False, before=0, after=6, spacing=1.5)

    _toc_styles(doc)

    return doc


def _toc_styles(doc) -> None:
    """Compact the styles Word uses for the generated contents lists.

    The default template already ships "toc 1".."toc 3" with 1.5 line spacing
    inherited from Normal, which stretches the lists over several extra pages.
    These are rewritten in place (by style id) so Word reuses them when the
    fields are refreshed.
    """
    specs = [
        ("TOCHeading", "TOC Heading", 14, True, 0, 12, 0),
        ("TOC1", "toc 1", 12, True, 10, 2, 0),
        ("TOC2", "toc 2", 12, False, 0, 2, 240),
        ("TOC3", "toc 3", 11.5, False, 0, 2, 480),
        ("TableofFigures", "Table of Figures", 11, False, 0, 3, 0),
    ]
    styles = doc.styles.element
    for style_id, name, size, bold, before, after, indent in specs:
        el = None
        for candidate in styles.findall(qn("w:style")):
            if candidate.get(qn("w:styleId")) == style_id:
                el = candidate
                break
        if el is None:
            el = parse_xml(
                f'<w:style {nsdecls("w")} w:type="paragraph" w:styleId="{style_id}">'
                f'<w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f'<w:next w:val="Normal"/></w:style>'
            )
            styles.append(el)
        for tag in ("w:pPr", "w:rPr"):
            old = el.find(qn(tag))
            if old is not None:
                el.remove(old)
        ind = f'<w:ind w:left="{indent}"/>' if indent else ""
        pPr = parse_xml(
            f'<w:pPr {nsdecls("w")}><w:spacing w:before="{int(before * 20)}" '
            f'w:after="{int(after * 20)}" w:line="240" w:lineRule="auto"/>'
            f"{ind}<w:jc w:val=\"left\"/></w:pPr>"
        )
        rPr = parse_xml(
            f'<w:rPr {nsdecls("w")}><w:rFonts w:ascii="Times New Roman" '
            f'w:hAnsi="Times New Roman"/><w:b w:val="{"true" if bold else "false"}"/>'
            f'<w:sz w:val="{int(size * 2)}"/><w:szCs w:val="{int(size * 2)}"/></w:rPr>'
        )
        el.append(pPr)
        el.append(rPr)


def _configure_heading(doc, name, size, centered, caps, before, after, italic=False):
    style = doc.styles[name]
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.italic = italic
    style.font.all_caps = caps
    style.font.color.rgb = INK
    rpr = style.element.get_or_add_rPr()
    rpr.rFonts.set(qn("w:ascii"), FONT)
    rpr.rFonts.set(qn("w:hAnsi"), FONT)
    pf = style.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    pf.keep_together = True


def _make_style(doc, name, size, centered, before, after, spacing):
    from docx.enum.style import WD_STYLE_TYPE

    style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.color.rgb = INK
    pf = style.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    return style


# ------------------------------------------------------------------ sections
def start_section(doc, fmt: str, start: int, numbered: bool = True):
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    sectPr = section._sectPr
    pg = sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), str(start))

    footer = section.footer
    footer.is_linked_to_previous = False
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)
    if numbered:
        field(para, "PAGE", "1")
        for run in para.runs:
            run.font.name = FONT
            run.font.size = Pt(11)
    return section


def suppress_footer(section) -> None:
    section.footer.is_linked_to_previous = False
    for p in section.footer.paragraphs:
        p.text = ""


# ------------------------------------------------------------------ elements
def para(doc, text="", bold=False, italic=False, size=None, align=None,
         space_after=None, space_before=None, indent=None, style=None, color=None):
    p = doc.add_paragraph(style=style)
    if text:
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        if size:
            run.font.size = Pt(size)
        if color is not None:
            run.font.color.rgb = color
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if space_before is not None:
        p.paragraph_format.space_before = Pt(space_before)
    if indent is not None:
        p.paragraph_format.first_line_indent = Inches(indent)
    return p


def rich(doc, parts, align=None, space_after=None, indent=None):
    """parts = list of (text, {bold/italic/sup/sub}) tuples."""
    p = doc.add_paragraph()
    for text, opts in parts:
        run = p.add_run(text)
        run.bold = opts.get("bold", False)
        run.italic = opts.get("italic", False)
        if opts.get("sup"):
            run.font.superscript = True
        if opts.get("sub"):
            run.font.subscript = True
        if opts.get("size"):
            run.font.size = Pt(opts["size"])
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        p.paragraph_format.first_line_indent = Inches(indent)
    return p


def bullets(doc, items, style="List Bullet"):
    for item in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.4
        if isinstance(item, tuple):
            lead, rest = item
            run = p.add_run(lead)
            run.bold = True
            p.add_run(rest)
        else:
            p.add_run(item)


def numbered(doc, items):
    bullets(doc, items, style="List Number")


def chapter(doc, number: int, title: str) -> None:
    label = doc.add_paragraph()
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label.paragraph_format.space_before = Pt(6)
    label.paragraph_format.space_after = Pt(2)
    run = label.add_run(f"CHAPTER {number}")
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = FONT

    head = doc.add_paragraph(style="Heading 1")
    head.add_run(f"{number}.  {title.upper()}")


def h2(doc, number: str, title: str) -> None:
    p = doc.add_paragraph(style="Heading 2")
    p.add_run(f"{number}  {title}")


def h3(doc, number: str, title: str) -> None:
    p = doc.add_paragraph(style="Heading 3")
    p.add_run(f"{number}  {title}")


def page_break(doc) -> None:
    """Start the next block on a fresh page without leaving an empty paragraph."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.page_break_before = True
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = Pt(1)
    run = p.add_run("")
    run.font.size = Pt(1)


def collapse_page_breaks(doc) -> None:
    """Merge leftover explicit page-break paragraphs into page_break_before.

    Older builds inserted a paragraph containing a manual break, which leaves a
    blank line (and sometimes a blank page) after the break. This pass moves the
    break onto the following paragraph and drops the empty one.
    """
    body = doc.element.body
    for para in list(body.iterchildren(qn("w:p"))):
        brs = para.findall(".//" + qn("w:br"))
        if not brs or any(b.get(qn("w:type")) != "page" for b in brs):
            continue
        nxt = para.getnext()
        if nxt is None or nxt.tag != qn("w:p"):
            continue
        pPr = nxt.find(qn("w:pPr"))
        if pPr is None:
            pPr = OxmlElement("w:pPr")
            nxt.insert(0, pPr)
        if pPr.find(qn("w:pageBreakBefore")) is None:
            el = OxmlElement("w:pageBreakBefore")
            pPr.append(el)
        body.remove(para)


def figure(doc, path: Path, number: str, caption: str, width_cm: float = 13.0,
           style: str = "Figure Caption") -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))

    cap = doc.add_paragraph(style=style)
    cap.add_run(f"Figure {number}: {caption}" if style == "Figure Caption" else f"Graph {number}: {caption}")
    _keep_with_next(cap, False)


def graph(doc, path: Path, number: str, caption: str, width_cm: float = 12.5) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))

    cap = doc.add_paragraph(style="Graph Caption")
    cap.add_run(f"Graph {number}: {caption}")


def table_caption(doc, number: str, caption: str) -> None:
    cap = doc.add_paragraph(style="Table Caption")
    cap.add_run(f"Table {number}: {caption}")
    _keep_with_next(cap, True)


def table(doc, headers, rows, widths=None, font_size=9.5, align="left",
          header_fill="EFE9DC", zebra=True, first_col_bold=False, pad=1.0) -> None:
    top = int(60 * pad)
    side = int(90 * pad)
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    _borders(tbl)

    hdr = tbl.rows[0]
    _repeat_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(str(text))
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.name = FONT
        _shade(cell, header_fill)
        _set_cell_margins(cell, top, top, side, side)

    for r_i, row in enumerate(rows):
        cells = tbl.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (i > 0 and align == "center") else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            run = p.add_run(str(value))
            run.font.size = Pt(font_size)
            run.font.name = FONT
            if first_col_bold and i == 0:
                run.bold = True
            _set_cell_margins(cell, top, top, side, side)
            if zebra and r_i % 2 == 1:
                _shade(cell, "F7F4EC")

    if widths:
        for row in tbl.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)

    # Keep short tables on one page; long ones may break but never inside a row.
    for row in tbl.rows:
        _cant_split(row)
    if len(tbl.rows) <= 11:
        _keep_rows_together(tbl)

    # small spacer
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 1.0
    return tbl


def callout(doc, text: str, label: str = "Note") -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    _borders(tbl, sz=4, color="C9401F")
    cell = tbl.rows[0].cells[0]
    _shade(cell, "FBF1EC")
    _set_cell_margins(cell, 120, 120, 160, 160)
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f"{label}: ")
    run.bold = True
    run.font.size = Pt(10.5)
    run2 = p.add_run(text)
    run2.font.size = Pt(10.5)


def toc_field(doc, kind: str = "toc") -> None:
    instructions = {
        "toc": ' TOC \\o "1-3" \\h \\z \\u ',
        "figure": ' TOC \\h \\z \\t "Figure Caption,1" ',
        "table": ' TOC \\h \\z \\t "Table Caption,1" ',
        "graph": ' TOC \\h \\z \\t "Graph Caption,1" ',
    }
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    field(p, instructions[kind], "Right-click and choose Update Field to build this list.")
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.name = FONT


def enable_update_fields(doc) -> None:
    settings = doc.settings.element
    node = settings.find(qn("w:updateFields"))
    if node is None:
        node = OxmlElement("w:updateFields")
        settings.append(node)
    node.set(qn("w:val"), "true")
