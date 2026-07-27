"""Inline text spans (rich text subset) + parse/serialize helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from md2docx.domain.scripts import iter_script_segments

ScriptKind = Literal["plain", "sub", "super"]


@dataclass
class TextSpan:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str | None = None
    script: ScriptKind = "plain"


def plain_spans(text: str) -> list[TextSpan]:
    if not text:
        return []
    return [TextSpan(text=text)]


def spans_to_plain(spans: list[TextSpan] | None, fallback: str = "") -> str:
    if not spans:
        return fallback
    return "".join(s.text for s in spans)


def _scripts_to_spans(
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    code: bool = False,
    link: str | None = None,
) -> list[TextSpan]:
    out: list[TextSpan] = []
    for kind, content in iter_script_segments(text):
        if not content and kind != "plain":
            continue
        if kind == "plain":
            if content:
                out.append(
                    TextSpan(
                        text=content,
                        bold=bold,
                        italic=italic,
                        code=code,
                        link=link,
                        script="plain",
                    )
                )
        elif kind in ("sub", "super"):
            out.append(
                TextSpan(
                    text=content,
                    bold=bold,
                    italic=italic,
                    code=code,
                    link=link,
                    script=kind,  # type: ignore[arg-type]
                )
            )
    return out


def parse_inline_to_spans(text: str) -> list[TextSpan]:
    """Parse **bold**, *italic*, `code`, [txt](url), and _/^ scripts."""
    if not text:
        return []
    spans: list[TextSpan] = []
    # tokenize: code, bold, italic, link, or plain chunk
    token = re.compile(
        r"(`([^`]+)`)"
        r"|(\*\*(.+?)\*\*)"
        r"|(\*(.+?)\*)"
        r"|(\[([^\]]+)\]\(([^)]+)\))"
        r"|([^*`\[]+|\*+|[`\[\]])"
    )
    pos = 0
    plain_buf: list[str] = []

    def flush_plain() -> None:
        nonlocal plain_buf
        if plain_buf:
            spans.extend(_scripts_to_spans("".join(plain_buf)))
            plain_buf = []

    for m in token.finditer(text):
        if m.start() > pos:
            plain_buf.append(text[pos : m.start()])
        if m.group(2) is not None:  # code
            flush_plain()
            spans.append(TextSpan(text=m.group(2), code=True))
        elif m.group(4) is not None:  # bold
            flush_plain()
            spans.extend(_scripts_to_spans(m.group(4), bold=True))
        elif m.group(6) is not None:  # italic
            flush_plain()
            spans.extend(_scripts_to_spans(m.group(6), italic=True))
        elif m.group(8) is not None:  # link
            flush_plain()
            spans.extend(_scripts_to_spans(m.group(8), link=m.group(9)))
        else:
            plain_buf.append(m.group(0))
        pos = m.end()
    if pos < len(text):
        plain_buf.append(text[pos:])
    flush_plain()
    return spans or plain_spans(text)


def spans_to_markdown(spans: list[TextSpan] | None, fallback: str = "") -> str:
    if not spans:
        return fallback
    parts: list[str] = []
    for s in spans:
        t = s.text
        if s.script == "sub":
            t = f"_{{{t}}}" if not re.fullmatch(r"[0-9A-Za-zА-Яа-яЁё]+", t) else f"_{t}"
        elif s.script == "super":
            t = f"^{{{t}}}" if not re.fullmatch(r"[0-9A-Za-zА-Яа-яЁё]+", t) else f"^{t}"
        if s.code:
            t = f"`{t}`"
        elif s.bold:
            t = f"**{t}**"
        elif s.italic:
            t = f"*{t}*"
        if s.link:
            t = f"[{t}]({s.link})"
        parts.append(t)
    return "".join(parts)
