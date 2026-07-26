from md2docx.domain.structural import is_structural_heading


def test_introduction():
    assert is_structural_heading("ВВЕДЕНИЕ")
    assert is_structural_heading("введение")


def test_numbered_section_not_structural():
    assert not is_structural_heading("1 Постановка задачи")


def test_appendix():
    assert is_structural_heading("ПРИЛОЖЕНИЕ А")
