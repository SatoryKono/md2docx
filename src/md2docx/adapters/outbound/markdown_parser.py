"""Markdown text → domain Blocks (outbound adapter / driving content source)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from md2docx.domain.model import (
    Block,
    CodeLine,
    EmptyLine,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    Table,
)
from md2docx.domain.scripts import strip_md_inline
from md2docx.domain.structural import is_structural_heading


class SimpleMarkdownParser:
    """Линейный парсер MD, совместимый с прежним convert_markdown_to_docx."""

    def __init__(self) -> None:
        self._pending_table_caption: str | None = None

    def parse(self, text: str) -> Sequence[Block]:
        self._pending_table_caption = None
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks: list[Block] = []
        i = 0
        in_code = False
        code_buf: list[str] = []
        para_buf: list[str] = []

        def flush_para() -> None:
            nonlocal para_buf
            if not para_buf:
                return
            joined = " ".join(para_buf).strip()
            if joined:
                blocks.append(Paragraph(text=joined))
            para_buf = []

        while i < len(lines):
            line = lines[i]

            if line.strip().startswith("```"):
                flush_para()
                if not in_code:
                    in_code = True
                    code_buf = []
                else:
                    in_code = False
                    for cl in code_buf:
                        blocks.append(CodeLine(text=cl if cl else " "))
                    code_buf = []
                i += 1
                continue
            if in_code:
                code_buf.append(line)
                i += 1
                continue

            if not line.strip():
                flush_para()
                i += 1
                continue

            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                flush_para()
                level = min(len(m.group(1)), 3)
                raw = strip_md_inline(m.group(2).strip())
                structural = level == 1 and is_structural_heading(raw)
                text_out = raw.upper() if structural else raw
                blocks.append(
                    Heading(level=level, text=text_out, structural=structural)
                )
                i += 1
                continue

            m = re.match(r"^(?:Table|Таблица)\s*:\s*(.*)$", line.strip(), re.I)
            if m:
                flush_para()
                cap = m.group(1).strip()
                if not re.match(r"^Таблица\s+\d+", cap, re.I):
                    cap = f"Таблица — {cap}" if cap else "Таблица"
                # caption stored on following table if possible; standalone as paragraph-like
                # We emit Table with empty rows only if no table follows — keep caption on next Table
                # For simplicity: store as Table caption-only by peeking ahead
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and "|" in lines[j]:
                    # attach later when table parsed — stash caption
                    self._pending_table_caption = strip_md_inline(cap)
                    i += 1
                    continue
                blocks.append(Table(rows=[], caption=strip_md_inline(cap)))
                i += 1
                continue

            m = re.match(r"^(?:Figure|Рисунок)\s*:\s*(.*)$", line.strip(), re.I)
            if m:
                flush_para()
                cap = m.group(1).strip()
                if not re.match(r"^Рисунок\s+\d+", cap, re.I):
                    cap = f"Рисунок — {cap}" if cap else "Рисунок"
                blocks.append(Figure(caption=strip_md_inline(cap), path=None))
                i += 1
                continue

            if "|" in line and i + 1 < len(lines) and re.match(
                r"^\s*\|?[\s\-:|]+\|", lines[i + 1]
            ):
                flush_para()
                rows: list[list[str]] = []
                while i < len(lines) and "|" in lines[i]:
                    raw = lines[i].strip()
                    if re.match(r"^\|?[\s\-:|]+\|?$", raw):
                        i += 1
                        continue
                    cells = [c.strip() for c in raw.strip("|").split("|")]
                    rows.append(cells)
                    i += 1
                cap = self._pending_table_caption
                self._pending_table_caption = None
                if rows:
                    blocks.append(Table(rows=rows, caption=cap))
                    blocks.append(EmptyLine())
                continue

            if line.lstrip().startswith(">"):
                flush_para()
                qparts: list[str] = []
                while i < len(lines) and lines[i].lstrip().startswith(">"):
                    qparts.append(re.sub(r"^\s*>\s?", "", lines[i]))
                    i += 1
                blocks.append(Quote(text=" ".join(qparts)))
                continue

            m = re.match(r"^\s*[-*+—–]\s+(.*)$", line)
            if m:
                flush_para()
                while i < len(lines):
                    m2 = re.match(r"^\s*[-*+—–]\s+(.*)$", lines[i])
                    if not m2:
                        break
                    item = strip_md_inline(m2.group(1)).lstrip("—–- \t")
                    blocks.append(ListItem(text=item, ordered=False))
                    i += 1
                continue

            m = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
            if m:
                flush_para()
                n = 1
                while i < len(lines):
                    m2 = re.match(r"^\s*\d+[.)]\s+(.*)$", lines[i])
                    if not m2:
                        break
                    item = strip_md_inline(m2.group(1))
                    blocks.append(ListItem(text=item, ordered=True, index=n))
                    n += 1
                    i += 1
                continue

            m = re.match(r"^\$\$(.+)\$\$$", line.strip())
            if m:
                flush_para()
                blocks.append(Formula(text=m.group(1).strip()))
                i += 1
                continue

            m = re.match(r"^!\[([^\]]*)\]\(([^)]*)\)\s*$", line.strip())
            if m:
                flush_para()
                alt = m.group(1).strip() or "Иллюстрация"
                path = m.group(2).strip() or None
                if not re.match(r"^Рисунок\s+\d+", alt, re.I):
                    alt = f"Рисунок — {alt}"
                blocks.append(EmptyLine())
                blocks.append(Figure(caption=alt, path=path))
                i += 1
                continue

            if re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", line.strip()):
                flush_para()
                i += 1
                continue

            para_buf.append(line.strip())
            i += 1

        flush_para()
        return blocks
