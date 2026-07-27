"""DOCX low-level helpers (split from former docx_engine)."""
from __future__ import annotations

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

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

def _get_style_by_name(doc: Document, name: str):
    """Lookup paragraph style by visible name only (no style_id → no UserWarning)."""
    for s in doc.styles:
        try:
            if s.type == WD_STYLE_TYPE.PARAGRAPH and s.name == name:
                return s
        except Exception:
            continue
    raise KeyError(name)


def _get_or_add_paragraph_style(doc: Document, name: str):
    try:
        return _get_style_by_name(doc, name)
    except KeyError:
        pass
    try:
        return doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    except ValueError:
        # race / already exists under same id
        return _get_style_by_name(doc, name)


def _strip_num_pr(style) -> None:
    """Убрать привязку к Word Numbering (буллеты/автонумерация)."""
    pPr = style.element.find(qn("w:pPr"))
    if pPr is None:
        return
    for child in list(pPr):
        if child.tag == qn("w:numPr"):
            pPr.remove(child)


def _set_run_font(
    style,
    *,
    font: str,
    size_pt: float,
    bold=False,
    italic=False,
    all_caps=False,
    color: RGBColor | None = HEADING_COLOR,
):
    f = style.font
    f.name = font
    f.size = Pt(size_pt)
    f.bold = bold
    f.italic = italic
    f.all_caps = all_caps
    if color is not None:
        f.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    # Убрать theme-шрифты (иначе Heading тянет Calibri/majorHAnsi)
    for attr in list(rfonts.attrib):
        local = attr.split("}")[-1] if "}" in attr else attr
        if local.endswith("Theme") or "theme" in local.lower():
            del rfonts.attrib[attr]
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font)
    # Явно чёрный в XML (сбрасывает themeColor у встроенных Heading)
    if color is not None:
        for child in list(rpr):
            if child.tag == qn("w:color"):
                rpr.remove(child)
        try:
            hex_val = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        except Exception:
            hex_val = "000000"
        rpr.append(rpr.makeelement(qn("w:color"), {qn("w:val"): hex_val}))


