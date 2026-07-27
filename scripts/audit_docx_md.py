#!/usr/bin/env python3
"""Аудит качества DOCX→MD (метрики из анализа A.docx).

  python scripts/audit_docx_md.py A.docx
  python scripts/audit_docx_md.py A.docx -o report.md --media-dir out_media
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# allow running without install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from md2docx.adapters.outbound.docx_reader import DocxReader, _is_toc_line
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import Figure, Heading, ListItem, Paragraph, Table


def audit(model, md: str) -> list[tuple[str, object, str]]:
    issues: list[tuple[str, object, str]] = []
    kinds = Counter(type(b).__name__ for b in model.blocks)

    empty_p = sum(
        1 for b in model.blocks if isinstance(b, Paragraph) and not b.text.strip()
    )
    if empty_p:
        issues.append(("empty_paragraphs", empty_p, "пустые Paragraph"))

    toc = [
        b.text
        for b in model.blocks
        if isinstance(b, Paragraph) and _is_toc_line(b.text)
    ]
    if toc:
        issues.append(("toc_leak", len(toc), "TOC-строки в body"))

    tables = [b for b in model.blocks if isinstance(b, Table)]
    caps = sum(1 for t in tables if t.caption)
    if tables and caps < max(1, len(tables) // 3):
        issues.append(
            ("table_captions", f"{caps}/{len(tables)}", "мало подписей таблиц")
        )

    figs = [b for b in model.blocks if isinstance(b, Figure)]
    with_path = sum(1 for f in figs if f.path)
    if figs and with_path == 0:
        issues.append(("figures_no_media", len(figs), "подписи без файлов"))

    h3 = sum(1 for b in model.blocks if isinstance(b, Heading) and b.level == 3)
    lists = sum(1 for b in model.blocks if isinstance(b, ListItem))

    print("=== metrics ===")
    print("blocks", len(model.blocks), dict(kinds))
    print("H3", h3, "ListItem", lists, "tables", len(tables), "captions", caps)
    print("figures", len(figs), "with_path", with_path)
    print("md_lines", len(md.splitlines()), "md_bytes", len(md.encode("utf-8")))
    print("=== issues ===")
    if not issues:
        print("(none critical by heuristics)")
    for code, n, msg in issues:
        print(f"- [{code}] {n}: {msg}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit DOCX→MD conversion")
    ap.add_argument("docx", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="write markdown")
    ap.add_argument("--media-dir", type=Path, default=None)
    ap.add_argument("--no-outline", action="store_true")
    args = ap.parse_args()
    if not args.docx.is_file():
        print("error: file not found", args.docx, file=sys.stderr)
        return 1

    reader = DocxReader(outline=not args.no_outline, media_dir=args.media_dir)
    model = reader.read(args.docx)
    md = serialize_document(model)
    if args.output:
        args.output.write_text(md, encoding="utf-8")
        print("wrote", args.output)
    audit(model, md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
