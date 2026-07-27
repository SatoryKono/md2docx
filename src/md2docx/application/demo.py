from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocumentWriter
from md2docx.domain.demo_document import build_demo_model
from md2docx.domain.stylespec import RenderOptions


class BuildDemo:
    def __init__(self, writer: DocumentWriter) -> None:
        self._writer = writer

    def execute(self, dest: Path, options: RenderOptions) -> Path:
        model = build_demo_model()
        return self._writer.write(model, options, dest)
