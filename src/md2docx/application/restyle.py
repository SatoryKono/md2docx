from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocumentWriter
from md2docx.domain.stylespec import RenderOptions


class RestyleDocx:
    def __init__(self, writer: DocumentWriter) -> None:
        self._writer = writer

    def execute(
        self,
        source: Path,
        dest: Path,
        options: RenderOptions,
    ) -> Path:
        return self._writer.restyle(source, dest, options)
