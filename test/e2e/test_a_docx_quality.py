"""Качество конвертации полного A.docx (если файл есть в корне)."""

from __future__ import annotations

from pathlib import Path

import pytest

from md2docx.adapters.outbound.docx_reader import DocxReader, _is_toc_line
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import (
    Figure,
    Heading,
    ListItem,
    Paragraph,
    SectionBreak,
    Table,
)

A_DOCX = Path(__file__).resolve().parents[2] / "A.docx"


@pytest.mark.skipif(not A_DOCX.is_file(), reason="A.docx not in repo root")
def test_a_docx_no_toc_leak_and_has_h3(tmp_path: Path):
    media = tmp_path / "media"
    model = DocxReader(outline=True, media_dir=media).read(A_DOCX)
    md = serialize_document(model)

    toc_paras = [b.text for b in model.blocks if isinstance(b, Paragraph) and _is_toc_line(b.text)]
    assert toc_paras == [], f"TOC leak: {toc_paras[:5]}"

    empty_p = sum(1 for b in model.blocks if isinstance(b, Paragraph) and not b.text.strip())
    assert empty_p == 0

    h3 = [b for b in model.blocks if isinstance(b, Heading) and b.level == 3]
    assert len(h3) >= 5, "Header4/5 should map to H3"

    h1 = [b for b in model.blocks if isinstance(b, Heading) and b.level == 1]
    assert any(b.text.strip().startswith("1") for b in h1)

    tables = [b for b in model.blocks if isinstance(b, Table)]
    assert len(tables) >= 10
    with_cap = sum(1 for t in tables if t.caption)
    assert with_cap >= 2

    figs = [b for b in model.blocks if isinstance(b, Figure)]
    assert len(figs) >= 10
    assert md.count("#") >= 20

    bib = [b for b in model.blocks if isinstance(b, ListItem) and b.ordered and b.index is not None]
    assert len(bib) >= 20

    # orientation preserved from multi-section A
    breaks = [b for b in model.blocks if isinstance(b, SectionBreak)]
    if breaks:
        assert any(b.setup.orientation == "landscape" for b in breaks)


@pytest.mark.skipif(not A_DOCX.is_file(), reason="A.docx not in repo root")
def test_a_docx_md_roundtrip_sample_stable(tmp_path: Path):
    """Фрагмент модели A: md→docx→md identity на каноне (без Table/Figure/Section)."""
    from md2docx.adapters.outbound.docx_writer import DocxWriter
    from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
    from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
    from md2docx.application.convert_docx import ConvertDocxToMarkdown
    from md2docx.application.convert_md import ConvertMarkdownToDocx
    from md2docx.domain.model import DocumentModel, TitleMeta
    from md2docx.domain.page import page_setup_default
    from md2docx.domain.stylespec import RenderOptions

    model = DocxReader(outline=True, media_dir=tmp_path / "m").read(A_DOCX)
    slim_blocks = [
        b
        for b in model.blocks[:60]
        if not isinstance(b, (Figure, Table, SectionBreak))
        and not (isinstance(b, Heading) and not (b.text or "").strip())
        and not (isinstance(b, Paragraph) and not (b.text or "").strip())
    ][:20]
    slim = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=slim_blocks,
    )
    md1 = serialize_document(slim, emit_default_section=False)
    docx = tmp_path / "slim.docx"
    ConvertMarkdownToDocx(SimpleMarkdownParser(), DocxWriter()).execute(
        md1, docx, RenderOptions(page_numbers=False)
    )
    ConvertDocxToMarkdown(DocxReader(outline=False), MarkdownWriter()).execute(
        docx, tmp_path / "back.md"
    )
    parser = SimpleMarkdownParser()
    blocks2 = [
        b
        for b in parser.parse((tmp_path / "back.md").read_text(encoding="utf-8"))
        if not isinstance(b, SectionBreak)
    ]
    md2 = serialize_document(
        DocumentModel(
            title=TitleMeta(),
            default_page=page_setup_default(),
            blocks=blocks2,
        ),
        emit_default_section=False,
    )
    assert md2 == md1
