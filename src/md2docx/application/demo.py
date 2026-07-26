from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocumentWriter
from md2docx.domain.stylespec import RenderOptions


class BuildDemo:
    def __init__(self, writer: DocumentWriter) -> None:
        self._writer = writer

    def execute(self, dest: Path, options: RenderOptions) -> Path:
        return self._writer.write_demo(options, dest)
