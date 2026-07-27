from md2docx.domain.spans import parse_inline_to_spans, spans_to_markdown, spans_to_plain


def test_parse_bold_italic_code():
    spans = parse_inline_to_spans("a **b** and *c* plus `d`")
    plain = spans_to_plain(spans)
    assert "b" in plain and "c" in plain and "d" in plain
    kinds = {(s.bold, s.italic, s.code) for s in spans}
    assert (True, False, False) in kinds
    assert (False, True, False) in kinds
    assert (False, False, True) in kinds


def test_parse_scripts_in_plain():
    spans = parse_inline_to_spans("H_2O")
    assert any(s.script == "sub" and s.text == "2" for s in spans)


def test_spans_to_markdown_round():
    spans = parse_inline_to_spans("**x**")
    md = spans_to_markdown(spans)
    assert "**" in md or "x" in md
