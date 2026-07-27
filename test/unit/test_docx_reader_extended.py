"""Unit: DocxReader — списки, формулы, multi-section, figures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.domain.model import (
    CodeLine,
    DocumentModel,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    SectionBreak,
    Table,
    TitleMeta,
)
from md2docx.domain.page import PageSetup, page_setup_default
from md2docx.domain.stylespec import RenderOptions


def test_reader_roundtrip_rich_model(tmp_path: Path):
    img = tmp_path / "x.png"
    Image.new("RGB", (100, 50), (1, 2, 3)).save(img)
    media = tmp_path / "media"
    model = DocumentModel(
        title=TitleMeta(org="ORG", topic="Topic", city_year="City – 2026"),
        default_page=page_setup_default(),
        blocks=[
            Heading(level=1, text="ВВЕДЕНИЕ", structural=True),
            Paragraph(text="Body"),
            ListItem(text="dash item", ordered=False),
            ListItem(text="num item", ordered=True, index=1),
            Table(rows=[["H1", "H2"], ["a", "b"]], caption="Таблица 1 — t"),
            Figure(caption="Рисунок 1 — f", path=str(img)),
            Formula(text="a+b"),
            Quote(text="quote text"),
            CodeLine(text="x=1"),
            SectionBreak(
                setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)
            ),
            Paragraph(text="land"),
        ],
    )
    src = tmp_path / "src.docx"
    DocxWriter().write(model, RenderOptions(page_numbers=False), src)

    got = DocxReader(outline=False, media_dir=media).read(src)
    kinds = {type(b).__name__ for b in got.blocks}
    assert "Heading" in kinds
    assert "Paragraph" in kinds
    assert "Table" in kinds
    assert "Figure" in kinds
    assert "SectionBreak" in kinds or any(
        isinstance(b, SectionBreak) for b in got.blocks
    )
    figs = [b for b in got.blocks if isinstance(b, Figure)]
    assert any(f.path for f in figs)
    # landscape break or default
    setups = [got.default_page] + [
        b.setup for b in got.blocks if isinstance(b, SectionBreak)
    ]
    assert any(s.orientation == "landscape" for s in setups)


def test_reader_outline_mode_still_reads_body(tmp_path: Path):
    model = DocumentModel(
        blocks=[
            Heading(level=1, text="ВВЕДЕНИЕ", structural=True),
            Paragraph(text="after intro"),
        ]
    )
    src = tmp_path / "o.docx"
    DocxWriter().write(model, RenderOptions(page_numbers=False), src)
    m = DocxReader(outline=True).read(src)
    texts = [getattr(b, "text", "") for b in m.blocks]
    assert any("ВВЕДЕНИЕ" in (t or "") for t in texts)
