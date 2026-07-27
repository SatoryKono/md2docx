#!/usr/bin/env python3
"""Собрать test/fixtures/a_fragment.docx из первого раздела тела A.docx.

Запуск из корня репозитория:
  python scripts/extract_a_fragment.py [path/to/A.docx]
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from md2docx.adapters.outbound.docx_reader import _paragraph_md_text, _style_name
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import (
    DocumentModel,
    Figure,
    Heading,
    Paragraph,
    Table,
    TitleMeta,
)
from md2docx.domain.structural import is_structural_heading
from md2docx.domain.stylespec import RenderOptions

ROOT = Path(__file__).resolve().parents[1]
OUT_DOCX = ROOT / "test" / "fixtures" / "a_fragment.docx"
OUT_MD = ROOT / "test" / "fixtures" / "a_fragment.expected.md"


def iter_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield "p", DocxParagraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "t", DocxTable(child, doc)


def extract(src_path: Path) -> DocumentModel:
    src = Document(str(src_path))
    blocks: list = []
    pending_cap: str | None = None
    capturing = False
    sections = 0
    paras = 0
    max_sections = 1

    for kind, obj in iter_blocks(src):
        if kind == "p":
            sn = _style_name(obj)
            raw = (obj.text or "").strip()
            if sn.startswith("toc") or sn.startswith("TOC"):
                continue
            if sn in ("Heading 1",) and raw and not capturing and not blocks:
                # mapped @Header1
                pass
            if (sn == "Heading 1" or sn == "StructuralHeading") and raw and not capturing:
                # first title-like
                if not any(isinstance(b, Heading) and b.structural for b in blocks):
                    if is_structural_heading(raw) or sn == "StructuralHeading":
                        text = raw.replace("\t", " ").strip()
                        blocks.append(Heading(level=1, text=text, structural=True))
                        continue
            # original names may still appear if alias not applied before map
            # _style_name already aliases @Header*
            if sn == "Heading 1" and raw and capturing is False:
                # section start: "1 …"
                if raw[:1].isdigit() or "\t" in (obj.text or ""):
                    sections += 1
                    if sections > max_sections:
                        break
                    capturing = True
            if sn == "Heading 1" and raw and not capturing:
                # @Header2 maps to Heading 1
                text = _paragraph_md_text(obj).replace("\t", " ").strip() or raw
                if text[:1].isdigit():
                    sections += 1
                    if sections > max_sections:
                        break
                    capturing = True
                    blocks.append(Heading(level=1, text=text, structural=False))
                    continue

            if not capturing:
                if sn == "StructuralHeading" and raw:
                    text = _paragraph_md_text(obj).replace("\t", " ").strip() or raw
                    blocks.append(Heading(level=1, text=text, structural=True))
                continue

            if not raw and sn != "CaptionTable":
                continue

            md = _paragraph_md_text(obj).replace("\t", " ").strip() or raw.replace(
                "\t", " "
            ).strip()

            if sn == "StructuralHeading":
                blocks.append(Heading(level=1, text=md, structural=True))
            elif sn == "Heading 1":
                blocks.append(
                    Heading(
                        level=1,
                        text=md,
                        structural=is_structural_heading(md),
                    )
                )
            elif sn == "Heading 2":
                blocks.append(Heading(level=2, text=md, structural=False))
            elif sn == "Heading 3":
                blocks.append(Heading(level=3, text=md, structural=False))
            elif sn == "CaptionTable":
                pending_cap = md
            elif sn == "CaptionFigure":
                blocks.append(Figure(caption=md, path=None))
            elif sn in ("Normal", "Bibliography"):
                if md:
                    blocks.append(Paragraph(text=md))
                    paras += 1
            if paras >= 3 and any(isinstance(b, Table) for b in blocks):
                break
        else:
            if not capturing:
                continue
            rows: list[list[str]] = []
            for row in obj.rows:
                seen: set[int] = set()
                cells: list[str] = []
                for cell in row.cells:
                    tid = id(cell._tc)
                    if tid in seen:
                        continue
                    seen.add(tid)
                    parts = [
                        _paragraph_md_text(p).strip()
                        for p in cell.paragraphs
                        if _paragraph_md_text(p).strip()
                    ]
                    cells.append(" ".join(parts))
                if any(cells):
                    rows.append(cells)
            if rows:
                rows = [r[:4] for r in rows[:5]]
                blocks.append(Table(rows=rows, caption=pending_cap))
                pending_cap = None
            if paras >= 2:
                break

    return DocumentModel(title=TitleMeta(), blocks=blocks)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "A.docx"
    if not src.is_file():
        print(f"error: not found {src}", file=sys.stderr)
        return 1
    model = extract(src)
    print(f"blocks: {len(model.blocks)}")
    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    DocxWriter().write(model, RenderOptions(page_numbers=False), OUT_DOCX)
    md = serialize_document(model)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_DOCX} ({OUT_DOCX.stat().st_size} bytes)")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
