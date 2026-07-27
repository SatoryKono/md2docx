"""DOCX low-level helpers (split from former docx_engine)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt, RGBColor

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

from md2docx.domain.page import PageSetup, page_setup_from_physical


def read_section_page_setup(section):
    """Считать PageSetup из секции Word (ориентация, размер, поля)."""
    from docx.enum.section import WD_ORIENT


    w = float(section.page_width.mm) if section.page_width else 210.0
    h = float(section.page_height.mm) if section.page_height else 297.0
    hint = (
        "landscape"
        if section.orientation == WD_ORIENT.LANDSCAPE or w > h + 0.5
        else "portrait"
    )
    return page_setup_from_physical(
        w,
        h,
        margin_left_mm=float(section.left_margin.mm) if section.left_margin else 30.0,
        margin_right_mm=float(section.right_margin.mm)
        if section.right_margin
        else 15.0,
        margin_top_mm=float(section.top_margin.mm) if section.top_margin else 20.0,
        margin_bottom_mm=float(section.bottom_margin.mm)
        if section.bottom_margin
        else 20.0,
        orientation_hint=hint,
    )


def apply_gost_page_setup(doc: Document, page: dict[str, float] | None = None) -> None:
    """Применить page dict ко **всем** секциям (portrait A4 по умолчанию).

    Для restyle существующих multi-section документов используйте
    save/restore через read_section_page_setup + set_section_page —
    иначе landscape-секции будут сброшены в portrait.
    """
    p = page or PAGE

    setup = PageSetup(
        orientation="portrait",
        width_mm=p.get("width_mm", 210),
        height_mm=p.get("height_mm", 297),
        margin_left_mm=p.get("left_mm", 30),
        margin_right_mm=p.get("right_mm", 15),
        margin_top_mm=p.get("top_mm", 20),
        margin_bottom_mm=p.get("bottom_mm", 20),
    )
    for section in doc.sections:
        set_section_page(section, setup)


def set_section_page(section, setup) -> None:
    """Ориентация + размер + поля для одной секции Word.

    Логический PageSetup: width×height как portrait (короткая×длинная).
    В Word при landscape page_width > page_height и orientation=LANDSCAPE.
    """
    from docx.enum.section import WD_ORIENT


    if not isinstance(setup, PageSetup):
        return
    n = setup.normalized()
    # Сначала ориентация, затем явные размеры (python-docx не всегда swap'ает сам)
    if n.orientation == "landscape":
        section.orientation = WD_ORIENT.LANDSCAPE
        # длинная сторона = width страницы в landscape
        section.page_width = Mm(n.height_mm)
        section.page_height = Mm(n.width_mm)
    else:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Mm(n.width_mm)
        section.page_height = Mm(n.height_mm)
    section.left_margin = Mm(n.margin_left_mm)
    section.right_margin = Mm(n.margin_right_mm)
    section.top_margin = Mm(n.margin_top_mm)
    section.bottom_margin = Mm(n.margin_bottom_mm)
    section.header_distance = Mm(10)
    section.footer_distance = Mm(10)
    try:
        section.different_first_page_header_footer = True
    except Exception:
        pass


def section_text_width_mm(section) -> float:
    """Ширина полосы набора = page_width − left − right (мм)."""
    try:
        return float(section.page_width.mm) - float(section.left_margin.mm) - float(
            section.right_margin.mm
        )
    except Exception:
        return 165.0  # A4 210−30−15


def section_text_height_mm(section) -> float:
    """Высота полосы набора = page_height − top − bottom (мм)."""
    try:
        return float(section.page_height.mm) - float(section.top_margin.mm) - float(
            section.bottom_margin.mm
        )
    except Exception:
        return 257.0  # A4 297−20−20


def add_figure_picture(doc: Document, image_path: str | Path, section) -> Any:
    """Вставить рисунок: ширина = полоса набора секции, с ограничением по высоте.

    - width = page_width − left − right (не меньше 20 мм, fallback 165);
    - если при полной ширине высота > (text_height − запас под подпись),
      масштабируем пропорционально, чтобы рисунок помещался на страницу;
    - сбрасываем firstLine/left/right indent абзаца (иначе Normal 1.25 см
      сдвигает inline-рисунок и он «вылезает» за правое поле).
    """
    text_w = section_text_width_mm(section)
    if text_w < 20:
        text_w = 165.0
    text_h = section_text_height_mm(section)
    # запас под подпись CaptionFigure (~1 строка + интервал)
    max_h = max(float(text_h) - 15.0, 40.0)

    shape = doc.add_picture(str(image_path), width=Mm(text_w))
    try:
        w_mm = float(shape.width.mm)
        h_mm = float(shape.height.mm)
        if h_mm > max_h and h_mm > 0:
            scale = max_h / h_mm
            shape.width = Mm(w_mm * scale)
            shape.height = Mm(max_h)
    except Exception:
        pass

    p = doc.paragraphs[-1]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    # явный 0 перекрывает firstLine=851 twips стиля Normal
    pf.first_line_indent = Pt(0)
    pf.left_indent = Pt(0)
    pf.right_indent = Pt(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    return shape


