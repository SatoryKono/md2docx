"""DOCX low-level helpers (split from former docx_engine)."""
from __future__ import annotations

from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor

from md2docx.domain.scripts import iter_script_segments, strip_md_inline
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


def _strip_md_inline(text: str) -> str:
    return strip_md_inline(text)


def add_runs_with_scripts(paragraph, text: str) -> None:
    """Добавить runs с поддержкой подстрочных (_) и надстрочных (^) индексов."""
    if not text:
        return
    for kind, content in iter_script_segments(text):
        if not content and kind != "plain":
            continue
        if kind == "plain":
            if content:
                paragraph.add_run(content)
        elif kind == "sub":
            run = paragraph.add_run(content)
            run.font.subscript = True
        elif kind == "super":
            run = paragraph.add_run(content)
            run.font.superscript = True


def add_runs_from_spans(paragraph, spans) -> None:
    """Render TextSpan list (bold/italic/code/link/script)."""
    if not spans:
        return
    for s in spans:
        run = paragraph.add_run(s.text or "")
        if s.bold or s.code:
            run.bold = True
        if s.italic:
            run.italic = True
        if s.script == "sub":
            run.font.subscript = True
        elif s.script == "super":
            run.font.superscript = True
        # link: text only in DOCX (no hyperlink XML for MVP subset)


def add_paragraph_formatted(
    doc: Document,
    text: str,
    *,
    style: str | None = None,
    spans=None,
) -> Any:
    p = doc.add_paragraph()
    if style:
        try:
            p.style = _get_style_by_name(doc, style)
        except KeyError:
            p.style = style
    if spans:
        add_runs_from_spans(p, spans)
    else:
        clean = strip_md_inline(text) if text else ""
        add_runs_with_scripts(p, clean)
    return p


