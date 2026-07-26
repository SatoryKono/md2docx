"""Deprecated shim. Use: python -m md2docx

Kept for backward compatibility with older scripts.
"""

from __future__ import annotations

import sys
import warnings

warnings.warn(
    "gost_styles_python_docx is deprecated; use `python -m md2docx` or package md2docx",
    DeprecationWarning,
    stacklevel=2,
)

from md2docx.adapters.inbound.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
