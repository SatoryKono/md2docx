"""E2E: ориентация portrait/landscape docx ↔ md."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
from md2docx.application.convert_docx import ConvertDocxToMarkdown
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.domain.model import (
    DocumentModel,
    Paragraph,
    SectionBreak,
    Table,
    TitleMeta,
)
from md2docx.domain.page import PageSetup, page_setup_default
from md2docx.domain.stylespec import RenderOptions


def _orients(path: Path) -> list[str]:
    doc = Document(str(path))
    out = []
    for s in doc.sections:
        w = float(s.page_width.mm)
        h = float(s.page_height.mm)
        if s.orientation == WD_ORIENT.LANDSCAPE or w > h + 0.5:
            out.append("landscape")
        else:
            out.append("portrait")
    return out


def test_writer_multi_section_orientation(tmp_path: Path):
    model = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=[
            Paragraph(text="Портрет текст"),
            SectionBreak(setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)),
            Table(
                rows=[["Col1", "Col2", "Col3"], ["a", "b", "c"]],
                caption="Таблица 1 — Landscape",
            ),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="Снова портрет"),
        ],
    )
    dest = tmp_path / "multi.docx"
    DocxWriter().write(model, RenderOptions(page_numbers=False), dest)
    orients = _orients(dest)
    assert len(orients) >= 2
    assert "landscape" in orients
    assert orients[0] == "portrait"
    assert orients[1] == "landscape"


def test_docx_md_docx_orientation(tmp_path: Path):
    # build source docx
    src_model = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=[
            Paragraph(text="До таблицы"),
            SectionBreak(setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)),
            Table(rows=[["X", "Y"], ["1", "2"]], caption="Таблица 1 — Wide"),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="После"),
        ],
    )
    src = tmp_path / "src.docx"
    DocxWriter().write(src_model, RenderOptions(page_numbers=False), src)
    assert "landscape" in _orients(src)

    md_path = tmp_path / "out.md"
    ConvertDocxToMarkdown(DocxReader(outline=False), MarkdownWriter()).execute(src, md_path)
    md = md_path.read_text(encoding="utf-8")
    assert "orientation=landscape" in md

    dst = tmp_path / "dst.docx"
    ConvertMarkdownToDocx(SimpleMarkdownParser(), DocxWriter()).execute(
        md, dst, RenderOptions(page_numbers=False)
    )
    o2 = _orients(dst)
    assert "landscape" in o2
    assert o2[0] == "portrait"
    assert o2 == _orients(src)


def test_restyle_preserves_orientation(tmp_path: Path):
    """restyle не должен сбрасывать landscape-секции в portrait."""
    src_model = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=[
            Paragraph(text="Портрет"),
            SectionBreak(setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)),
            Table(rows=[["A", "B"], ["1", "2"]], caption="Таблица 1 — Wide"),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="Снова портрет"),
        ],
    )
    src = tmp_path / "src.docx"
    dst = tmp_path / "restyled.docx"
    DocxWriter().write(src_model, RenderOptions(page_numbers=False), src)
    before = _orients(src)
    assert before == ["portrait", "landscape", "portrait"]

    DocxWriter().restyle(src, dst, RenderOptions(page_numbers=True))
    after = _orients(dst)
    assert after == before
    assert "landscape" in after


def test_reader_writer_orientation_sequence(tmp_path: Path):
    """docx → model → docx сохраняет чередование P/L (после merge одинаковых)."""
    src_model = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=[
            Paragraph(text="P0"),
            SectionBreak(setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)),
            Paragraph(text="L1"),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="P2"),
            SectionBreak(setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)),
            Paragraph(text="L3"),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="P4"),
        ],
    )
    src = tmp_path / "src.docx"
    DocxWriter().write(src_model, RenderOptions(page_numbers=False), src)
    expected = ["portrait", "landscape", "portrait", "landscape", "portrait"]
    assert _orients(src) == expected

    model = DocxReader(outline=False).read(src)
    breaks = [b for b in model.blocks if isinstance(b, SectionBreak)]
    assert any(b.setup.orientation == "landscape" for b in breaks)

    dst = tmp_path / "out.docx"
    DocxWriter().write(model, RenderOptions(page_numbers=False), dst)
    assert _orients(dst) == expected
