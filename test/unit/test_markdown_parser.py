from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import DocumentModel, Heading, ListItem, Table


def test_parse_heading_and_list():
    md = """# ВВЕДЕНИЕ

Текст.

- пункт один
- пункт два

# 1 Раздел

| a | b |
|---|---|
| 1 | 2 |
"""
    blocks = list(SimpleMarkdownParser().parse(md))
    types = [type(b).__name__ for b in blocks]
    assert "Heading" in types
    assert "ListItem" in types
    assert "Table" in types
    h0 = next(b for b in blocks if isinstance(b, Heading) and b.structural)
    assert h0.text == "ВВЕДЕНИЕ"
    items = [b for b in blocks if isinstance(b, ListItem)]
    assert len(items) == 2
    assert items[0].ordered is False


def test_hash_legend_not_heading():
    """«# – достоверность…» — легенда (символ #), не ATX Heading."""
    md = """Примечание: * – достоверность различия (P < 0,05) с группой интактных животных,

# – достоверность различия (P < 0,05) с группой ложной патологии,

& – достоверность различия (P < 0,05) с контролем.

# 1 Настоящий раздел

\\# – экранированная легенда
"""
    blocks = list(SimpleMarkdownParser().parse(md))
    from md2docx.domain.model import Heading, Paragraph

    paras = [b for b in blocks if isinstance(b, Paragraph)]
    heads = [b for b in blocks if isinstance(b, Heading)]
    legend = [
        p
        for p in paras
        if "ложной патологии" in (p.text or "") or p.text.startswith("# –")
    ]
    assert legend, "legend must stay Paragraph"
    assert all(
        "достоверн" in (p.text or "").lower() or p.text.startswith("#")
        for p in legend
    )
    # real heading still works
    assert any(h.level == 1 and "Настоящий" in h.text for h in heads)
    # must NOT turn legend into Heading (loses leading #)
    assert not any("ложной патологии" in (h.text or "") for h in heads)


def test_table_br_cells_roundtrip():
    """Ячейки с <br> / newlines сохраняют число строк таблицы."""
    model = DocumentModel(
        blocks=[
            Table(
                rows=[
                    ["H1", "H2"],
                    ["a", "line1<br>line2"],
                    ["Радикулопатическая<br>боль", "x"],
                ]
            )
        ]
    )
    md = serialize_document(model, emit_default_section=False)
    blocks = list(SimpleMarkdownParser().parse(md))
    tables = [b for b in blocks if isinstance(b, Table)]
    assert len(tables) == 1
    t = tables[0]
    assert len(t.rows) == 3
    assert len(t.rows[1]) == 2
    assert "line1" in t.rows[1][1] and "line2" in t.rows[1][1]
    assert "Радикулопатическая" in t.rows[2][0]
    assert "боль" in t.rows[2][0]
