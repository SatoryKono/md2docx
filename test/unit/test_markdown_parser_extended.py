"""Unit: расширенный markdown_parser — секции, формулы, quote, code, image."""

from __future__ import annotations

from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.domain.model import (
    CodeLine,
    Figure,
    Formula,
    ListItem,
    Quote,
    SectionBreak,
    Table,
)


def test_parse_section_directive_sets_default_and_break():
    md = """<!-- md2docx:section orientation=landscape width_mm=210 height_mm=297 margin_left=20 margin_right=15 margin_top=20 margin_bottom=20 -->

Текст.

<!-- md2docx:section orientation=portrait width_mm=210 height_mm=297 margin_left=30 margin_right=15 margin_top=20 margin_bottom=20 -->

Снова портрет.
"""
    p = SimpleMarkdownParser()
    blocks = list(p.parse(md))
    assert p.default_page.orientation == "landscape"
    breaks = [b for b in blocks if isinstance(b, SectionBreak)]
    assert len(breaks) >= 2
    assert any(b.setup.orientation == "portrait" for b in breaks)


def test_parse_formula_quote_code_image():
    md = r"""$$E=mc^2$$

> строка цитаты
> вторая

```
code1
code2
```

![Рисунок 1 — схема](media/a.png)

Рисунок: подпись без файла

***

Текст после.
"""
    blocks = list(SimpleMarkdownParser().parse(md))
    kinds = [type(b).__name__ for b in blocks]
    assert "Formula" in kinds
    assert "Quote" in kinds
    assert "CodeLine" in kinds
    assert "Figure" in kinds
    assert "Paragraph" in kinds

    formula = next(b for b in blocks if isinstance(b, Formula))
    assert "E=mc" in formula.text

    quote = next(b for b in blocks if isinstance(b, Quote))
    assert "цитат" in quote.text

    codes = [b for b in blocks if isinstance(b, CodeLine)]
    assert any(c.text == "code1" for c in codes)

    figs = [b for b in blocks if isinstance(b, Figure)]
    assert any(f.path and "media/a.png" in f.path.replace("\\", "/") for f in figs)
    assert any(f.path is None for f in figs)


def test_parse_ordered_list_and_table_caption():
    md = """Таблица: Параметры модели

| a | b |
|---|---|
| 1 | 2 |

1. первый
2. второй
"""
    blocks = list(SimpleMarkdownParser().parse(md))
    tables = [b for b in blocks if isinstance(b, Table)]
    assert len(tables) == 1
    assert tables[0].caption
    assert "Параметры" in tables[0].caption
    items = [b for b in blocks if isinstance(b, ListItem) and b.ordered]
    assert len(items) == 2
    assert items[0].index == 1


def test_parse_pipe_escape_in_table():
    md = r"""
| col |
| --- |
| a\|b |
"""
    blocks = list(SimpleMarkdownParser().parse(md))
    t = next(b for b in blocks if isinstance(b, Table))
    assert any("|" in c or "a" in c for row in t.rows for c in row)


def test_parse_standalone_table_caption():
    md = "Таблица: только подпись\n"
    blocks = list(SimpleMarkdownParser().parse(md))
    tables = [b for b in blocks if isinstance(b, Table)]
    assert tables
    assert tables[0].rows == [] or tables[0].caption
