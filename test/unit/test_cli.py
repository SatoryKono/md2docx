from pathlib import Path

from md2docx.adapters.inbound.cli import default_output_for, main


def test_list_styles_exit_0():
    assert main(["--list-styles"]) == 0


def test_missing_input_exit_1(tmp_path: Path, capsys):
    missing = tmp_path / "nope.md"
    code = main(["-i", str(missing), "-o", str(tmp_path / "out.docx"), "-q"])
    assert code == 1
    err = capsys.readouterr().err
    assert "не найден" in err


def test_unsupported_suffix_exit_2(tmp_path: Path):
    bad = tmp_path / "file.xyz"
    bad.write_text("x", encoding="utf-8")
    code = main(["-i", str(bad), "-o", str(tmp_path / "out.docx"), "-q"])
    assert code == 2


def test_docx_to_docx_without_restyle_exit_2(tmp_path: Path):
    # minimal valid empty-ish: create via demo first
    demo = tmp_path / "demo.docx"
    assert main(["--demo", "-o", str(demo), "-q"]) == 0
    out = tmp_path / "out.docx"
    code = main(["-i", str(demo), "-o", str(out), "-q"])
    assert code == 2


def test_md_to_docx_happy(tmp_path: Path):
    md = tmp_path / "in.md"
    md.write_text("# ВВЕДЕНИЕ\n\nТекст.\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    assert main(["-i", str(md), "-o", str(out), "-q"]) == 0
    assert out.is_file()


def test_docx_to_md_happy(tmp_path: Path):
    demo = tmp_path / "demo.docx"
    assert main(["--demo", "-o", str(demo), "-q"]) == 0
    out = tmp_path / "out.md"
    assert main(["-i", str(demo), "-o", str(out), "-q"]) == 0
    assert out.is_file()
    assert out.read_text(encoding="utf-8").strip()


def test_default_output_for():
    assert default_output_for("a.md", False).endswith(".docx")
    assert default_output_for("a.docx", False).endswith(".md")
    assert default_output_for(None, True) == "gost-demo.docx"


def test_strict_missing_image_exit_1(tmp_path: Path, capsys):
    md = tmp_path / "img.md"
    md.write_text(
        "![Рисунок — x](missing-image-xyz.png)\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    code = main(["-i", str(md), "-o", str(out), "--strict", "-q"])
    assert code == 1
    err = capsys.readouterr().err
    assert "изображение" in err.lower() or "не найден" in err.lower()


def test_non_strict_missing_image_still_writes(tmp_path: Path, capsys):
    md = tmp_path / "img.md"
    md.write_text(
        "![Рисунок — x](missing-image-xyz.png)\n\nТекст.\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    code = main(["-i", str(md), "-o", str(out), "-q"])
    assert code == 0
    assert out.is_file()
    err = capsys.readouterr().err
    assert "warning:" in err
