from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import (
    CodeLine,
    DocumentModel,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    Table,
    TitleMeta,
)


def test_serialize_heading_list_table():
    model = DocumentModel(
        blocks=[
            Heading(level=1, text="ВВЕДЕНИЕ", structural=True),
            Paragraph(text="Текст H_2O"),
            ListItem(text="один", ordered=False),
            ListItem(text="два", ordered=False),
            ListItem(text="шаг", ordered=True, index=1),
            Table(rows=[["a", "b"], ["1", "2"]], caption="Таблица — демо"),
        ]
    )
    md = serialize_document(model, emit_default_section=False)
    assert "# ВВЕДЕНИЕ" in md
    assert "Текст H_2O" in md or "Текст H_2O" in md
    assert "- один" in md
    assert "1. шаг" in md
    assert "| a | b |" in md
    assert "Таблица" in md


def test_serialize_formula_quote_code_figure():
    model = DocumentModel(
        blocks=[
            Formula(text="E=mc^2"),
            Quote(text="цитата"),
            CodeLine(text="print(1)"),
            Figure(caption="Рисунок — схема", path=None),
        ]
    )
    md = serialize_document(model, emit_default_section=False)
    assert "$$E=mc^2$$" in md
    assert "> цитата" in md
    assert "```" in md
    assert "print(1)" in md
    assert "Рисунок" in md


def test_serialize_title_front_matter():
    model = DocumentModel(
        title=TitleMeta(org="ОРГ", topic="Тема", city_year="Москва – 2026"),
        blocks=[Paragraph(text="тело")],
    )
    md = serialize_document(model, include_title=True, emit_default_section=False)
    assert md.startswith("---")
    assert "org: ОРГ" in md
    assert "topic: Тема" in md
    assert "тело" in md


def test_serialize_scripts_roundtrip_form():
    model = DocumentModel(blocks=[Paragraph(text="H_2O and x^2")])
    md = serialize_document(model, emit_default_section=False)
    assert "H_2O" in md
    assert "x^2" in md


def test_serialize_deterministic():
    model = DocumentModel(
        blocks=[
            Heading(level=1, text="1 Раздел", structural=False),
            Paragraph(text="a"),
        ]
    )
    a = serialize_document(model, emit_default_section=False)
    b = serialize_document(model, emit_default_section=False)
    assert a == b


def test_serialize_table_newlines_become_br():
    """Переносы в ячейках не должны ломать GFM table (одна строка MD = одна row)."""
    model = DocumentModel(
        blocks=[
            Table(
                rows=[
                    ["Уровень", "Описание"],
                    [
                        "Биасный агонизм",
                        "полный агонист Ca²⁺-пути,\nнеактивен по cAMP",
                    ],
                    ["Радикулопатическая \nболь", "данные"],
                ]
            )
        ]
    )
    md = serialize_document(model, emit_default_section=False)
    assert "\nнеактивен" not in md  # raw newline inside cell gone
    assert "<br>" in md
    # ровно 1 header + 1 separator + 2 data rows with leading |
    data_rows = [
        ln for ln in md.splitlines() if ln.startswith("|") and "---" not in ln
    ]
    assert len(data_rows) == 3


def test_serialize_hash_legend_escaped():
    model = DocumentModel(
        blocks=[
            Paragraph(
                text="# – достоверность различия (P < 0,05) с группой ложной патологии,"
            )
        ]
    )
    md = serialize_document(model, emit_default_section=False)
    assert md.startswith("\\# – достоверность")
    # round-trip through parser
    from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
    from md2docx.domain.model import Paragraph as P

    blocks = list(SimpleMarkdownParser().parse(md))
    paras = [b for b in blocks if isinstance(b, P)]
    assert paras
    assert paras[0].text.startswith("# – достоверность")


def test_serialize_figure_path_posix():
    model = DocumentModel(
        blocks=[Figure(caption="Рисунок 1 — x", path=r"A_media\image_001.png")]
    )
    md = serialize_document(model, emit_default_section=False)
    assert "A_media/image_001.png" in md
    assert "A_media\\image_001.png" not in md
