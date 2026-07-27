from md2docx.domain.scripts import (
    iter_script_segments,
    segments_to_markdown,
    strip_md_inline,
    text_roundtrip_scripts,
)


def _flags(text: str) -> list[tuple[str, str]]:
    return list(iter_script_segments(text))


def test_h2o_subscript_digit_only():
    segs = _flags("H_2O")
    assert segs == [("plain", "H"), ("sub", "2"), ("plain", "O")]


def test_superscript():
    segs = _flags("mc^2")
    assert segs == [("plain", "mc"), ("super", "2")]


def test_braced():
    segs = _flags("x_{i+1}^{2}")
    assert ("sub", "i+1") in segs
    assert ("super", "2") in segs


def test_escape_literals():
    segs = _flags(r"a\_b\^c")
    assert segs == [("plain", "a_b^c")]


def test_strip_keeps_scripts():
    assert "_2" in strip_md_inline("**H**_2O")


def test_segments_roundtrip_encode():
    assert text_roundtrip_scripts("H_2O") == "H_2O"
    assert text_roundtrip_scripts("x_{i+1}") == "x_{i+1}"
    assert segments_to_markdown([("plain", "E="), ("super", "2")]) == "E=^2"
