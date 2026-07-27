from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import DocumentModel, Paragraph, SectionBreak, Table, TitleMeta
from md2docx.domain.page import (
    PageSetup,
    page_setup_default,
    page_setup_from_physical,
    parse_section_directive_attrs,
)


def test_parse_directive_landscape():
    s = parse_section_directive_attrs(
        "orientation=landscape width_mm=297 height_mm=210 margin_left=20"
    )
    assert s.orientation == "landscape"
    assert abs(s.width_mm - 210) < 0.1 or abs(s.width_mm - 297) < 0.1
    n = s.normalized()
    assert n.width_mm <= n.height_mm
    assert n.orientation == "landscape"


def test_physical_landscape():
    s = page_setup_from_physical(297, 210, orientation_hint="landscape")
    assert s.orientation == "landscape"
    w, h = s.physical_size_mm()
    assert w > h


def test_md_section_roundtrip():
    model = DocumentModel(
        title=TitleMeta(),
        default_page=page_setup_default(),
        blocks=[
            Paragraph(text="Книжная"),
            SectionBreak(
                setup=PageSetup(orientation="landscape", width_mm=210, height_mm=297)
            ),
            Table(rows=[["A", "B"], ["1", "2"]], caption="Таблица 1 — Широкая"),
            SectionBreak(setup=page_setup_default()),
            Paragraph(text="Снова книжная"),
        ],
    )
    md = serialize_document(model)
    assert "orientation=landscape" in md
    parser = SimpleMarkdownParser()
    blocks = list(parser.parse(md))
    breaks = [b for b in blocks if isinstance(b, SectionBreak)]
    assert any(b.setup.orientation == "landscape" for b in breaks)
    md2 = serialize_document(
        DocumentModel(
            title=TitleMeta(),
            default_page=parser.default_page,
            blocks=blocks,
        )
    )
    assert "orientation=landscape" in md2
