from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocumentWriter, MarkdownParser
from md2docx.domain.model import DocumentModel, TitleMeta
from md2docx.domain.stylespec import RenderOptions


class ConvertMarkdownToDocx:
    def __init__(self, parser: MarkdownParser, writer: DocumentWriter) -> None:
        self._parser = parser
        self._writer = writer

    def execute(
        self,
        markdown: str,
        dest: Path,
        options: RenderOptions,
        *,
        title: TitleMeta | None = None,
    ) -> Path:
        blocks = list(self._parser.parse(markdown))
        model = DocumentModel(title=title or TitleMeta(), blocks=blocks)
        return self._writer.write(model, options, dest)
