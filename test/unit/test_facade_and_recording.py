from pathlib import Path

from md2docx import __version__, convert_md_to_docx
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.recording_writer import RecordingDocumentWriter
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.domain.demo_document import build_demo_model
from md2docx.domain.stylespec import RenderOptions


def test_version():
    assert __version__


def test_recording_writer_use_case(tmp_path: Path):
    rec = RecordingDocumentWriter()
    out = tmp_path / "x.docx"
    ConvertMarkdownToDocx(SimpleMarkdownParser(), rec).execute(
        "# ВВЕДЕНИЕ\n\nHi\n", out, RenderOptions()
    )
    assert rec.models
    assert out.is_file()
    assert "blocks" in out.read_text(encoding="utf-8")


def test_demo_model_nonempty():
    m = build_demo_model()
    assert m.title.org
    assert m.blocks


def test_facade_md_to_docx(tmp_path: Path):
    dest = tmp_path / "out.docx"
    convert_md_to_docx("# ВВЕДЕНИЕ\n\nText\n", dest)
    assert dest.is_file()
