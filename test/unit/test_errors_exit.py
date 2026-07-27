from pathlib import Path

from md2docx.adapters.inbound.cli import main
from md2docx.domain.errors import (
    InputNotFoundError,
    MediaError,
    StyleConfigError,
    UnsupportedFormatError,
)


def test_error_exit_codes():
    assert InputNotFoundError("x").exit_code == 1
    assert UnsupportedFormatError("x").exit_code == 2
    assert StyleConfigError("x").exit_code == 3
    assert MediaError("x").exit_code == 1


def test_cli_missing_uses_typed_path(tmp_path: Path, capsys):
    code = main(["-i", str(tmp_path / "no.md"), "-o", str(tmp_path / "o.docx"), "-q"])
    assert code == 1


def test_cli_bad_suffix(tmp_path: Path):
    f = tmp_path / "a.xyz"
    f.write_text("x", encoding="utf-8")
    assert main(["-i", str(f), "-o", str(tmp_path / "o.docx"), "-q"]) == 2
