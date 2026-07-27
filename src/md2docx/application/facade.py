"""Library API (без argparse)."""

from __future__ import annotations

from pathlib import Path

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.json_style_repo import JsonStyleRepository
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
from md2docx.application.convert_docx import ConvertDocxToMarkdown
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.application.demo import BuildDemo
from md2docx.application.restyle import RestyleDocx
from md2docx.domain.model import TitleMeta
from md2docx.domain.stylespec import RenderOptions, default_render_options


def convert_md_to_docx(
    markdown: str | Path,
    dest: Path | str,
    *,
    options: RenderOptions | None = None,
    title: TitleMeta | None = None,
    config: Path | str | None = None,
) -> Path:
    """Markdown text or .md path → .docx."""
    if isinstance(markdown, Path) or (
        isinstance(markdown, str) and Path(markdown).is_file() and "\n" not in markdown
    ):
        text = Path(markdown).read_text(encoding="utf-8")
    else:
        text = str(markdown)
    opts = options or default_render_options()
    if config is not None:
        pack = JsonStyleRepository().load(config)
        opts = RenderOptions(
            font=pack.font,
            body_pt=pack.body_pt,
            table_pt=pack.table_pt,
            small_pt=pack.small_pt,
            line_spacing=pack.line_spacing,
            first_line_mm=pack.first_line_mm,
            page=dict(pack.page),
            page_numbers=opts.page_numbers,
            strict=opts.strict,
            style_pack=pack,
        )
    return ConvertMarkdownToDocx(SimpleMarkdownParser(), DocxWriter()).execute(
        text, Path(dest), opts, title=title
    )


def convert_docx_to_md(
    source: Path | str,
    dest: Path | str,
    *,
    include_title: bool = False,
    outline: bool = True,
    media_dir: str | Path | None = None,
) -> Path:
    reader = DocxReader(outline=outline, media_dir=media_dir)
    return ConvertDocxToMarkdown(reader, MarkdownWriter()).execute(
        Path(source), Path(dest), include_title=include_title
    )


def restyle_docx(
    source: Path | str,
    dest: Path | str,
    *,
    options: RenderOptions | None = None,
) -> Path:
    return RestyleDocx(DocxWriter()).execute(
        Path(source), Path(dest), options or default_render_options()
    )


def build_demo_docx(
    dest: Path | str,
    *,
    options: RenderOptions | None = None,
) -> Path:
    return BuildDemo(DocxWriter()).execute(Path(dest), options or default_render_options())
