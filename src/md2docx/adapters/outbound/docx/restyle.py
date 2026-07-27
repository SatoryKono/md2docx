"""DOCX low-level helpers (split from former docx_engine)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

from md2docx.adapters.outbound.docx.page import read_section_page_setup, set_section_page
from md2docx.adapters.outbound.docx.page_numbers import setup_page_numbers
from md2docx.adapters.outbound.docx.styles import apply_gost_styles


def _collect_used_style_ids(doc: Document) -> set[str]:
    """Собрать w:styleId, реально используемые в документе."""
    used: set[str] = set()

    def add_from_p_element(p_elm) -> None:
        pPr = p_elm.find(qn("w:pPr"))
        if pPr is not None:
            pStyle = pPr.find(qn("w:pStyle"))
            if pStyle is not None:
                val = pStyle.get(qn("w:val"))
                if val:
                    used.add(val)
        for r in p_elm.findall(qn("w:r")):
            rPr = r.find(qn("w:rPr"))
            if rPr is None:
                continue
            rStyle = rPr.find(qn("w:rStyle"))
            if rStyle is not None:
                val = rStyle.get(qn("w:val"))
                if val:
                    used.add(val)

    def walk_block_container(container) -> None:
        try:
            for p in container.paragraphs:
                add_from_p_element(p._element)
        except Exception:
            pass
        try:
            for table in container.tables:
                tbl = table._tbl
                tblPr = getattr(tbl, "tblPr", None)
                if tblPr is not None:
                    ts = tblPr.find(qn("w:tblStyle"))
                    if ts is not None:
                        val = ts.get(qn("w:val"))
                        if val:
                            used.add(val)
                for row in table.rows:
                    for cell in row.cells:
                        walk_block_container(cell)
        except Exception:
            pass

    walk_block_container(doc)
    for section in doc.sections:
        for attr in (
            "header",
            "footer",
            "first_page_header",
            "first_page_footer",
            "even_page_header",
            "even_page_footer",
        ):
            try:
                part = getattr(section, attr, None)
                if part is not None:
                    walk_block_container(part)
            except Exception:
                continue

    # всегда оставляем базовые
    used.add("Normal")
    used.add("DefaultParagraphFont")
    return {u for u in used if u}


def _expand_style_dependencies(styles_elm, used: set[str]) -> set[str]:
    """Добавить basedOn / link / next для используемых стилей."""
    by_id = {}
    for style in styles_elm.findall(qn("w:style")):
        sid = style.get(qn("w:styleId"))
        if sid:
            by_id[sid] = style

    changed = True
    while changed:
        changed = False
        for sid in list(used):
            style = by_id.get(sid)
            if style is None:
                continue
            for tag in ("basedOn", "link", "next"):
                el = style.find(qn(f"w:{tag}"))
                if el is None:
                    continue
                val = el.get(qn("w:val"))
                if val and val not in used:
                    used.add(val)
                    changed = True
    return used


def remove_unused_styles(doc: Document) -> int:
    """Удалить из styles.xml стили, не используемые в документе.

    Сохраняет used + цепочку basedOn/link/next + Normal.
    Возвращает число удалённых w:style.
    """
    styles_elm = doc.styles.element
    used = _collect_used_style_ids(doc)
    used = _expand_style_dependencies(styles_elm, used)

    removed = 0
    for style in list(styles_elm.findall(qn("w:style"))):
        sid = style.get(qn("w:styleId"))
        if not sid:
            continue
        if sid in used:
            continue
        # не трогаем docDefaults / latent без id уже отфильтрованы
        styles_elm.remove(style)
        removed += 1
    return removed


def restyle_docx(
    input_path: str | Path,
    output_path: str | Path,
    *,
    style_opts: dict[str, Any] | None = None,
    page_numbers: bool = True,
    prune_styles: bool = True,
) -> str:
    """Открыть существующий .docx, наложить стили ГОСТ, сохранить.

    Ориентация, размер и поля **каждой** секции сохраняются (multi-section
    portrait/landscape не сбрасываются в portrait A4).

    prune_styles: удалить неиспользуемые определения стилей из документа.
    """
    doc = Document(str(input_path))
    # apply_gost_styles → apply_gost_page_setup ставит portrait на все секции;
    # заранее снимаем PageSetup и возвращаем после стилей.
    saved_pages = [read_section_page_setup(s) for s in doc.sections]
    apply_gost_styles(doc, **(style_opts or {}))
    for section, setup in zip(doc.sections, saved_pages):
        set_section_page(section, setup)
    if page_numbers:
        setup_page_numbers(doc)
    if prune_styles:
        remove_unused_styles(doc)
    out = str(output_path)
    doc.save(out)
    return out

