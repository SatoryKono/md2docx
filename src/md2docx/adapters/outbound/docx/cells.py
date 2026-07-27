"""DOCX low-level helpers (split from former docx_engine)."""

from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor, Twips

from md2docx.domain.stylespec import (
    A_LINE_100,
    A_TABLE_CELL_PAD_PT,
    PAGE_DEFAULT,
)

PAGE = PAGE_DEFAULT
HEADING_COLOR = RGBColor(0x00, 0x00, 0x00)

ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "both": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

from md2docx.adapters.outbound.docx.helpers import _get_style_by_name
from md2docx.adapters.outbound.docx.runs import add_runs_with_scripts
from md2docx.domain.scripts import strip_md_inline as _strip_md_inline


def apply_cell_paragraph_spacing(paragraphs, pad_pt: float = A_TABLE_CELL_PAD_PT) -> None:
    """Отступы в ячейке: 1 абзац → 3pt сверху и снизу;
    несколько → первый 3pt сверху, последний 3pt снизу, остальные 0."""
    n = len(paragraphs)
    if n == 0:
        return
    for i, p in enumerate(paragraphs):
        pf = p.paragraph_format
        if n == 1:
            pf.space_before = Pt(pad_pt)
            pf.space_after = Pt(pad_pt)
        else:
            pf.space_before = Pt(pad_pt if i == 0 else 0)
            pf.space_after = Pt(pad_pt if i == n - 1 else 0)


def fill_table_cell(
    cell,
    text: str,
    *,
    style_name: str = "TableCell",
    pad_pt: float = A_TABLE_CELL_PAD_PT,
    doc: Document | None = None,
) -> None:
    """Заполнить ячейку текстом (\\n = новый абзац) и выставить отступы.
    Поддерживает _подстрочные_ и ^надстрочные индексы."""
    parts = text.split("\n") if text is not None else [""]
    if not parts:
        parts = [""]
    while len(cell.paragraphs) > 1:
        p = cell.paragraphs[-1]
        p._element.getparent().remove(p._element)
    cell.paragraphs[0].text = ""

    style_obj = None
    if doc is not None:
        try:
            style_obj = _get_style_by_name(doc, style_name)
        except KeyError:
            style_obj = None

    def _apply_style(paragraph) -> None:
        if style_obj is not None:
            paragraph.style = style_obj
        else:
            # last resort — may warn if name matches style_id only
            try:
                paragraph.style = style_name
            except Exception:
                pass

    _apply_style(cell.paragraphs[0])
    add_runs_with_scripts(cell.paragraphs[0], _strip_md_inline(parts[0]))
    for part in parts[1:]:
        p = cell.add_paragraph()
        _apply_style(p)
        add_runs_with_scripts(p, _strip_md_inline(part))
    apply_cell_paragraph_spacing(cell.paragraphs, pad_pt=pad_pt)


def add_empty_line(doc: Document) -> None:
    """Пустая строка-отбивка (после таблицы / перед рисунком)."""
    p = doc.add_paragraph("")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = A_LINE_100
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.left_indent = Pt(0)


def _set_paragraph(
    style,
    *,
    alignment: str,
    first_line_mm: float | None = 0,
    left_mm: float | None = 0,
    right_mm: float | None = 0,
    first_line_twips: int | None = None,
    left_twips: int | None = None,
    hanging_twips: int | None = None,
    before_pt: float = 0,
    after_pt: float = 0,
    line_spacing: float = 1.5,
    keep_with_next: bool = False,
    page_break_before: bool = False,
    outline_level: int | None = None,
):
    pf = style.paragraph_format
    pf.alignment = ALIGN[alignment]
    pf.space_before = Pt(before_pt)
    pf.space_after = Pt(after_pt)
    pf.keep_with_next = keep_with_next
    pf.page_break_before = page_break_before
    pf.line_spacing = line_spacing
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE

    if hanging_twips is not None:
        left = left_twips if left_twips is not None else hanging_twips
        pf.left_indent = Twips(left)
        pf.first_line_indent = Twips(-hanging_twips)
    elif first_line_twips is not None or left_twips is not None:
        pf.left_indent = Twips(left_twips or 0)
        pf.first_line_indent = Twips(first_line_twips or 0)
    else:
        pf.first_line_indent = Mm(first_line_mm or 0)
        pf.left_indent = Mm(left_mm or 0)

    pf.right_indent = Mm(right_mm or 0)
    if outline_level is not None:
        pPr = style.element.get_or_add_pPr()
        for child in list(pPr):
            if child.tag == qn("w:outlineLvl"):
                pPr.remove(child)
        el = pPr.makeelement(qn("w:outlineLvl"), {qn("w:val"): str(outline_level)})
        pPr.append(el)
