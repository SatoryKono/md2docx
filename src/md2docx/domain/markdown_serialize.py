"""DocumentModel → канонический Markdown (для round-trip)."""

from __future__ import annotations

import re
from pathlib import Path

from md2docx.domain.model import (
    CodeLine,
    DocumentModel,
    EmptyLine,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    SectionBreak,
    Table,
)
from md2docx.domain.page import PageSetup, page_setup_default
from md2docx.domain.scripts import text_roundtrip_scripts
from md2docx.domain.spans import spans_to_markdown


def _txt(s: str) -> str:
    return text_roundtrip_scripts(s) if s else s


def _escape_md_paragraph(text: str) -> str:
    """Экранировать абзацы, которые MD-парсер иначе примет за разметку.

    Пример: «# – достоверность различия (P < 0,05) с группой ложной патологии»
    — это легенда рисунка (символ #), а не ATX-заголовок.
    """
    if re.match(r"^#{1,6}(\s|$)", text):
        return "\\" + text
    return text


def _section_directive(setup: PageSetup) -> str:
    return f"<!-- md2docx:section {setup.to_directive_attrs()} -->"


def serialize_document(
    model: DocumentModel,
    *,
    include_title: bool = False,
    emit_default_section: bool = True,
) -> str:
    """Детерминированный MD. Пустые строки-разделители — по правилам блоков."""
    lines: list[str] = []

    if include_title:
        t = model.title
        if t.org or t.topic or t.city_year:
            lines.append("---")
            if t.org:
                lines.append(f"org: {t.org}")
            if t.topic:
                lines.append(f"topic: {t.topic}")
            if t.city_year:
                lines.append(f"city_year: {t.city_year}")
            lines.append("---")
            lines.append("")

    default = (model.default_page or page_setup_default()).normalized()
    # Явная секция 0, если не portrait A4 default или всегда для round-trip
    if emit_default_section:
        # emit if non-default OR first block is not SectionBreak
        first_is_break = any(isinstance(b, SectionBreak) for b in model.blocks[:1])
        if not first_is_break:
            std = page_setup_default()
            if default.differs_from(std) or any(isinstance(b, SectionBreak) for b in model.blocks):
                lines.append(_section_directive(default))
                lines.append("")

    blocks = [b for b in model.blocks if not isinstance(b, EmptyLine)]
    i = 0
    prev_setup = default
    while i < len(blocks):
        b = blocks[i]

        if isinstance(b, SectionBreak):
            setup = b.setup.normalized()
            if setup.differs_from(prev_setup):
                _ensure_blank_before(lines)
                lines.append(_section_directive(setup))
                lines.append("")
            prev_setup = setup
            i += 1
            continue

        if isinstance(b, Heading):
            ht = (b.text or "").strip()
            if not ht:
                i += 1
                continue
            _ensure_blank_before(lines)
            level = 1 if b.structural else max(1, min(b.level, 3))
            lines.append(f"{'#' * level} {_txt(ht)}")
            lines.append("")
            i += 1
            continue

        if isinstance(b, Paragraph):
            if getattr(b, "spans", None):
                pt = spans_to_markdown(b.spans, b.text or "")
            else:
                pt = (b.text or "").strip()
                pt = _escape_md_paragraph(_txt(pt)) if pt else ""
            if not (pt or "").strip():
                i += 1
                continue
            _ensure_blank_before(lines)
            lines.append(pt if getattr(b, "spans", None) else pt)
            lines.append("")
            i += 1
            continue

        if isinstance(b, ListItem):
            _ensure_blank_before(lines)
            n = 1
            while i < len(blocks) and isinstance(blocks[i], ListItem):
                item = blocks[i]
                assert isinstance(item, ListItem)
                if item.ordered:
                    idx = item.index if item.index is not None else n
                    lines.append(f"{idx}. {_txt(item.text)}")
                    n = idx + 1
                else:
                    lines.append(f"- {_txt(item.text)}")
                i += 1
            lines.append("")
            continue

        if isinstance(b, Table):
            _ensure_blank_before(lines)
            if b.caption:
                # Parser accepts «Таблица: …» and full «Таблица N — …»
                cap = _txt(b.caption)
                if not cap.lower().startswith("таблица"):
                    lines.append(f"Таблица: {cap}")
                else:
                    # keep full caption via prefix form for stable parse
                    lines.append(f"Таблица: {cap}")
                lines.append("")
            if b.rows:

                def _cell(c: str) -> str:
                    # Newlines break GFM tables (parser sees new rows).
                    # Reader uses <br> for multi-para cells; keep that and
                    # also normalize raw \\n / \\r from soft breaks.
                    s = _txt(c) if c else ""
                    s = s.replace("\r\n", "\n").replace("\r", "\n")
                    s = s.replace("\n", "<br>")
                    # escape pipes so MD tables survive round-trip
                    return s.replace("|", "\\|")

                rows = [[_cell(c) for c in row] for row in b.rows]
                width = max(len(r) for r in rows)
                norm = [r + [""] * (width - len(r)) for r in rows]
                lines.append("| " + " | ".join(norm[0]) + " |")
                lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
                for row in norm[1:]:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
            i += 1
            continue

        if isinstance(b, Figure):
            _ensure_blank_before(lines)
            cap = _txt(b.caption) if b.caption else "Рисунок"
            if b.path:
                # path + caption: image syntax; caption text as alt
                # POSIX separators — стабильнее для round-trip на Windows
                alt = cap.replace("]", "")
                path_s = Path(str(b.path)).as_posix()
                lines.append(f"![{alt}]({path_s})")
            else:
                lines.append(f"Рисунок: {cap}")
            lines.append("")
            i += 1
            continue

        if isinstance(b, Formula):
            _ensure_blank_before(lines)
            lines.append(f"$${_txt(b.text)}$$")
            lines.append("")
            i += 1
            continue

        if isinstance(b, Quote):
            _ensure_blank_before(lines)
            for part in _txt(b.text).split("\n"):
                lines.append(f"> {part}" if part else ">")
            lines.append("")
            i += 1
            continue

        if isinstance(b, CodeLine):
            _ensure_blank_before(lines)
            lines.append("```")
            while i < len(blocks) and isinstance(blocks[i], CodeLine):
                cl = blocks[i]
                assert isinstance(cl, CodeLine)
                lines.append(cl.text if cl.text != " " else "")
                i += 1
            lines.append("```")
            lines.append("")
            continue

        i += 1

    # trailing single newline
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def _ensure_blank_before(lines: list[str]) -> None:
    if lines and lines[-1] != "":
        lines.append("")
