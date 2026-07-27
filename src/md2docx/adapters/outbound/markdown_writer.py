"""DocumentModel → .md file."""

from __future__ import annotations

from pathlib import Path

from md2docx.domain.markdown_serialize import serialize_document
from md2docx.domain.model import DocumentModel


class MarkdownWriter:
    def write(
        self,
        model: DocumentModel,
        dest: Path,
        *,
        include_title: bool = False,
    ) -> Path:
        dest = Path(dest)
        text = serialize_document(model, include_title=include_title)
        dest.write_text(text, encoding="utf-8", newline="\n")
        return dest
