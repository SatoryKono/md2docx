from __future__ import annotations

from pathlib import Path

from md2docx.application.ports import DocumentRestyler
from md2docx.domain.stylespec import RenderOptions


class RestyleDocx:
    def __init__(self, restyler: DocumentRestyler) -> None:
        self._restyler = restyler

    def execute(
        self,
        source: Path,
        dest: Path,
        options: RenderOptions,
    ) -> Path:
        return self._restyler.restyle(source, dest, options)
