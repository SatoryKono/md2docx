from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.domain.model import Heading, ListItem, Paragraph, Table


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
