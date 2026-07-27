"""md2docx — Markdown ↔ DOCX (ГОСТ 7.32–2017 / стили A.docx), hexagonal layout."""

from md2docx.application.facade import (
    build_demo_docx,
    convert_docx_to_md,
    convert_md_to_docx,
    restyle_docx,
)

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "build_demo_docx",
    "convert_docx_to_md",
    "convert_md_to_docx",
    "restyle_docx",
]
