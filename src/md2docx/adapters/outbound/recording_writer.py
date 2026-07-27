"""Test double: DocumentWriter that records models (no python-docx)."""

from __future__ import annotations

from pathlib import Path

from md2docx.domain.model import DocumentModel
from md2docx.domain.stylespec import RenderOptions


class RecordingDocumentWriter:
    def __init__(self) -> None:
        self.models: list[DocumentModel] = []
        self.options: list[RenderOptions] = []
        self.dests: list[Path] = []

    def write(
        self,
        model: DocumentModel,
        options: RenderOptions,
        dest: Path,
    ) -> Path:
        self.models.append(model)
        self.options.append(options)
        dest = Path(dest)
        self.dests.append(dest)
        dest.write_text(f"recording:{len(model.blocks)} blocks\n", encoding="utf-8")
        return dest
