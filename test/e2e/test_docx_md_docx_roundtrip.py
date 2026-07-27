"""E2E: docx → md → docx → md на фрагменте A.docx.

Фикстура `test/fixtures/a_fragment.docx` собрана из первого раздела тела A.docx
(заголовки @Header1–3, таблица, абзацы @Common), пересохранена стилями md2docx.
"""

from __future__ import annotations

from pathlib import Path

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
from md2docx.application.convert_docx import ConvertDocxToMarkdown
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.stylespec import RenderOptions

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
A_FRAGMENT = FIXTURES / "a_fragment.docx"


def _docx_to_canonical_md(docx_path: Path, tmp: Path, name: str) -> str:
    md_path = tmp / name
    # outline=False: фикстура a_fragment уже «чистая», титул сохраняем
    ConvertDocxToMarkdown(DocxReader(outline=False), MarkdownWriter()).execute(docx_path, md_path)
    text = md_path.read_text(encoding="utf-8")
    blocks = list(SimpleMarkdownParser().parse(text))
    from md2docx.domain.model import DocumentModel, TitleMeta

    return serialize_document(DocumentModel(title=TitleMeta(), blocks=blocks))


def test_a_fragment_fixture_exists():
    assert A_FRAGMENT.is_file(), (
        f"Нет фикстуры {A_FRAGMENT}. Сгенерируйте из A.docx (scripts/extract_a_fragment.py)."
    )
    assert A_FRAGMENT.stat().st_size > 1000


def test_docx_md_docx_identity_a_fragment(tmp_path: Path):
    """docx (A-fragment) → md → docx → md: канонические MD совпадают."""
    options = RenderOptions(page_numbers=False)

    md1 = _docx_to_canonical_md(A_FRAGMENT, tmp_path, "from_a.md")
    assert md1.strip(), "MD из фрагмента A.docx пуст"
    assert "# " in md1 or "## " in md1

    # md → docx
    mid_docx = tmp_path / "mid.docx"
    ConvertMarkdownToDocx(SimpleMarkdownParser(), DocxWriter()).execute(md1, mid_docx, options)
    assert mid_docx.is_file()

    # docx → md again
    md2 = _docx_to_canonical_md(mid_docx, tmp_path, "round2.md")

    assert md2 == md1, (
        f"docx→md→docx→md mismatch (A.docx fragment)\n--- md1 ---\n{md1!r}\n--- md2 ---\n{md2!r}\n"
    )


def test_docx_md_docx_cli_a_fragment(tmp_path: Path):
    from md2docx.adapters.inbound.cli import main

    md1 = tmp_path / "1.md"
    d2 = tmp_path / "2.docx"
    md2 = tmp_path / "2.md"

    assert main(["-i", str(A_FRAGMENT), "-o", str(md1), "-q"]) == 0
    assert main(["-i", str(md1), "-o", str(d2), "-q"]) == 0
    assert main(["-i", str(d2), "-o", str(md2), "-q"]) == 0

    c1 = _docx_to_canonical_md(A_FRAGMENT, tmp_path, "c1.md")
    # re-canonize md2
    blocks = list(SimpleMarkdownParser().parse(md2.read_text(encoding="utf-8")))
    from md2docx.domain.model import DocumentModel, TitleMeta

    c2 = serialize_document(DocumentModel(title=TitleMeta(), blocks=blocks))
    assert c2 == c1


def test_a_fragment_contains_table_and_body():
    model = DocxReader().read(A_FRAGMENT)
    kinds = {type(b).__name__ for b in model.blocks}
    assert "Heading" in kinds
    assert "Paragraph" in kinds
    assert "Table" in kinds
    # content smoke from A.docx section 1
    texts = " ".join(
        getattr(b, "text", "") or getattr(b, "caption", "") or "" for b in model.blocks
    )
    assert "QPCT" in texts or "боли" in texts or "болев" in texts.lower()
