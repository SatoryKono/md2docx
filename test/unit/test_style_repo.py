from pathlib import Path

from md2docx.adapters.outbound.json_style_repo import JsonStyleRepository
from md2docx.domain.errors import StyleConfigError


def test_load_package_default():
    pack = JsonStyleRepository().load()
    assert pack.font
    assert pack.body_pt > 0
    assert pack.page["left_mm"] == 30


def test_load_missing_raises(tmp_path: Path):
    try:
        JsonStyleRepository().load(tmp_path / "nope.json")
        assert False, "expected StyleConfigError"
    except StyleConfigError:
        pass


def test_load_custom(tmp_path: Path):
    p = tmp_path / "s.json"
    p.write_text(
        '{"defaults":{"font":"Arial","body_size_pt":14,"line_spacing":1.2,'
        '"first_line_indent_mm":10},'
        '"page":{"width_mm":210,"height_mm":297,"margins_mm":{"left":25,"right":15,"top":20,"bottom":20}},'
        '"styles":[]}',
        encoding="utf-8",
    )
    pack = JsonStyleRepository().load(p)
    assert pack.font == "Arial"
    assert pack.body_pt == 14
    assert pack.page["left_mm"] == 25
