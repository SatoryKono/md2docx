"""DOCX low-level helpers (split from former docx_engine)."""

from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

from md2docx.domain.stylespec import (
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


def add_page_number_field(paragraph) -> None:
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char_sep = OxmlElement("w:fldChar")
    fld_char_sep.set(qn("w:fldCharType"), "separate")
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_begin)
    run._r.append(instr)
    run._r.append(fld_char_sep)
    run._r.append(fld_char_end)


def setup_page_numbers(doc: Document) -> None:
    """Номера страниц в нижнем колонтитуле (все секции).

    В документах вроде A.docx footer может быть пустым (0 paragraphs) —
    тогда создаём абзац, иначе IndexError.
    """
    for section in doc.sections:
        footer = section.footer
        try:
            footer.is_linked_to_previous = False
        except Exception:
            pass
        if not footer.paragraphs:
            fp = footer.add_paragraph()
        else:
            fp = footer.paragraphs[0]
            fp.clear()
        try:
            fp.style = _get_style_by_name(doc, "FooterPageNumber")
        except KeyError:
            pass
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_page_number_field(fp)
