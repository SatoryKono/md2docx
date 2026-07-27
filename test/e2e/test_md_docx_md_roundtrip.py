"""E2E: md → docx → md, идентичность канонического Markdown."""

from __future__ import annotations

from pathlib import Path

import pytest

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
from md2docx.application.convert_docx import ConvertDocxToMarkdown
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import DocumentModel, TitleMeta
from md2docx.domain.stylespec import RenderOptions

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _canonical_md(text: str) -> str:
    """MD → model → serialize (канон для сравнения)."""
    blocks = list(SimpleMarkdownParser().parse(text))
    model = DocumentModel(title=TitleMeta(), blocks=blocks)
    return serialize_document(model, include_title=False)


def _roundtrip(md_text: str, tmp_path: Path) -> tuple[str, str]:
    options = RenderOptions(page_numbers=False)
    docx_path = tmp_path / "mid.docx"
    md_out_path = tmp_path / "out.md"

    canonical = _canonical_md(md_text)
    ConvertMarkdownToDocx(SimpleMarkdownParser(), DocxWriter()).execute(
        canonical, docx_path, options
    )
    ConvertDocxToMarkdown(DocxReader(), MarkdownWriter()).execute(
        docx_path, md_out_path
    )
    out = md_out_path.read_text(encoding="utf-8")
    # нормализуем перевод строк
    out_canon = _canonical_md(out)
    return canonical, out_canon


@pytest.mark.parametrize(
    "name",
    [
        "roundtrip_basic.md",
        "roundtrip_scripts.md",
    ],
)
def test_md_docx_md_identity(name: str, tmp_path: Path):
    src = (FIXTURES / name).read_text(encoding="utf-8")
    expected, actual = _roundtrip(src, tmp_path)
    assert actual == expected, (
        f"round-trip mismatch for {name}\n"
        f"--- expected ---\n{expected!r}\n"
        f"--- actual ---\n{actual!r}\n"
    )


def test_cli_docx_to_md(tmp_path: Path):
    from md2docx.adapters.inbound.cli import main

    md = (FIXTURES / "roundtrip_scripts.md").read_text(encoding="utf-8")
    # write canonical through library first
    can = _canonical_md(md)
    md_path = tmp_path / "in.md"
    docx_path = tmp_path / "mid.docx"
    out_md = tmp_path / "back.md"
    md_path.write_text(can, encoding="utf-8")

    assert main(["-i", str(md_path), "-o", str(docx_path), "-q"]) == 0
    assert main(["-i", str(docx_path), "-o", str(out_md), "-q"]) == 0
    assert _canonical_md(out_md.read_text(encoding="utf-8")) == can


def test_serialize_parse_identity_for_fixtures():
    """Фикстуры после parse→serialize стабильны (основа e2e)."""
    for name in ("roundtrip_basic.md", "roundtrip_scripts.md"):
        raw = (FIXTURES / name).read_text(encoding="utf-8")
        once = _canonical_md(raw)
        twice = _canonical_md(once)
        assert once == twice, name
