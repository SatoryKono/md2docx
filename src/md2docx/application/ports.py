"""Порты (Protocol) — границы hexagon."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from md2docx.domain.model import Block, DocumentModel
from md2docx.domain.stylespec import RenderOptions


class MarkdownParser(Protocol):
    def parse(self, text: str) -> Sequence[Block]: ...


class DocumentWriter(Protocol):
    def write(
        self,
        model: DocumentModel,
        options: RenderOptions,
        dest: Path,
    ) -> Path: ...

    def restyle(
        self,
        source: Path,
        dest: Path,
        options: RenderOptions,
    ) -> Path: ...

    def write_demo(self, options: RenderOptions, dest: Path) -> Path: ...
