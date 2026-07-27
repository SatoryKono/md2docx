from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocxReader, MarkdownWriter


class ConvertDocxToMarkdown:
    def __init__(self, reader: DocxReader, writer: MarkdownWriter) -> None:
        self._reader = reader
        self._writer = writer

    def execute(
        self,
        source: Path,
        dest: Path,
        *,
        include_title: bool = False,
    ) -> Path:
        model = self._reader.read(source)
        return self._writer.write(model, dest, include_title=include_title)
