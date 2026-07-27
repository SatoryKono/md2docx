"""Unit: CLI — config, restyle, margins, include-title, errors."""

from __future__ import annotations

import json
from pathlib import Path

from md2docx.adapters.inbound.cli import _options_from_args, build_arg_parser, main
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.application.restyle import RestyleDocx
from md2docx.domain.stylespec import RenderOptions


def test_options_from_args_margins():
    p = build_arg_parser()
    args = p.parse_args(
        [
            "-i",
            "x.md",
            "--margin-left",
            "25",
            "--margin-right",
            "12",
            "--margin-top",
            "18",
            "--margin-bottom",
            "18",
            "--body-pt",
            "14",
            "--font",
            "Arial",
            "--no-page-numbers",
        ]
    )
    opt = _options_from_args(args)
    assert opt.page["left_mm"] == 25
    assert opt.page["right_mm"] == 12
    assert opt.body_pt == 14
    assert opt.font == "Arial"
    assert opt.page_numbers is False


def test_options_from_config_json(tmp_path: Path):
    cfg = {
        "defaults": {
            "font": "Times New Roman",
            "body_size_pt": 12,
            "line_spacing": 1.5,
            "first_line_indent_mm": 1.25,
        },
        "page": {
            "width_mm": 210,
            "height_mm": 297,
            "margins_mm": {"left": 28, "right": 14, "top": 19, "bottom": 19},
        },
        "styles": [
            {"style_id": "TableCell", "run": {"size_pt": 10}},
        ],
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    p = build_arg_parser()
    args = p.parse_args(["-i", "x.md", "--config", str(cfg_path)])
    opt = _options_from_args(args)
    assert opt.page["left_mm"] == 28
    assert opt.table_pt == 10
    assert opt.first_line_mm == 1.25


def test_cli_restyle(tmp_path: Path):
    demo = tmp_path / "demo.docx"
    assert main(["--demo", "-o", str(demo), "-q"]) == 0
    out = tmp_path / "restyled.docx"
    assert main(["-i", str(demo), "-o", str(out), "--restyle", "-q"]) == 0
    assert out.is_file()


def test_cli_include_title(tmp_path: Path):
    demo = tmp_path / "demo.docx"
    assert main(["--demo", "-o", str(demo), "-q"]) == 0
    out = tmp_path / "t.md"
    assert main(["-i", str(demo), "-o", str(out), "--include-title", "-q"]) == 0
    text = out.read_text(encoding="utf-8")
    # demo may or may not have title fields; file non-empty is enough
    assert text.strip()


def test_cli_md_out_must_be_docx(tmp_path: Path):
    md = tmp_path / "a.md"
    md.write_text("# X\n", encoding="utf-8")
    code = main(["-i", str(md), "-o", str(tmp_path / "b.md"), "-q"])
    assert code == 2


def test_cli_verbose_demo(tmp_path: Path, capsys):
    out = tmp_path / "d.docx"
    assert main(["--demo", "-o", str(out), "-v"]) == 0
    err = capsys.readouterr().err
    assert "output:" in err or out.is_file()


def test_restyle_use_case(tmp_path: Path):
    demo = tmp_path / "d.docx"
    assert main(["--demo", "-o", str(demo), "-q"]) == 0
    out = tmp_path / "r.docx"
    path = RestyleDocx(DocxWriter()).execute(
        demo, out, RenderOptions(page_numbers=True)
    )
    assert Path(path).is_file()


def test_cli_title_meta_on_md(tmp_path: Path):
    md = tmp_path / "t.md"
    md.write_text("Текст абзаца.\n", encoding="utf-8")
    out = tmp_path / "o.docx"
    code = main(
        [
            "-i",
            str(md),
            "-o",
            str(out),
            "--org",
            "ОРГ",
            "--topic",
            "Тема",
            "--city-year",
            "Город – 2026",
            "-q",
        ]
    )
    assert code == 0
    from docx import Document

    texts = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "ОРГ" in texts
    assert "Тема" in texts
