"""Порты (Protocol) — границы hexagon."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from md2docx.domain.model import Block, DocumentModel
from md2docx.domain.stylespec import RenderOptions, StylePack


class MarkdownParser(Protocol):
    def parse(self, text: str) -> Sequence[Block]: ...


class DocumentWriter(Protocol):
    def write(
        self,
        model: DocumentModel,
        options: RenderOptions,
        dest: Path,
    ) -> Path: ...


class DocumentRestyler(Protocol):
    def restyle(
        self,
        source: Path,
        dest: Path,
        options: RenderOptions,
    ) -> Path: ...


class DocxReader(Protocol):
    def read(self, path: Path | str) -> DocumentModel: ...


class MarkdownWriter(Protocol):
    def write(
        self,
        model: DocumentModel,
        dest: Path,
        *,
        include_title: bool = False,
    ) -> Path: ...


class StyleRepository(Protocol):
    def load(self, path: Path | str | None = None) -> StylePack: ...
