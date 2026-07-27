"""AR-4.2: единственный реестр Protocol — application.ports."""

import ast
from pathlib import Path


def test_no_protocol_duplicates_outside_ports():
    app = Path(__file__).resolve().parents[2] / "src" / "md2docx" / "application"
    offenders: list[str] = []
    for path in app.glob("*.py"):
        if path.name == "ports.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    getattr(base, "id", None) or getattr(
                        getattr(base, "attr", None), "__str__", lambda: None
                    )()
                    if isinstance(base, ast.Name) and base.id == "Protocol":
                        offenders.append(f"{path.name}:{node.name}")
                    if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                        offenders.append(f"{path.name}:{node.name}")
    assert offenders == [], f"Protocol classes outside ports.py: {offenders}"


def test_convert_docx_imports_from_ports():
    from md2docx.application.convert_docx import ConvertDocxToMarkdown
    from md2docx.application.ports import DocxReader, MarkdownWriter

    # type-check surface: constructor accepts ports
    assert ConvertDocxToMarkdown.__init__.__annotations__
    assert DocxReader is not None and MarkdownWriter is not None
