"""Подстрочные (_) и надстрочные (^) индексы — чистая логика без python-docx."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence


def strip_md_inline(text: str) -> str:
    """Снятие ** * ` ссылок. Одиночные _ и ^ сохраняются (индексы)."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def iter_script_segments(text: str) -> Iterator[tuple[str, str]]:
    """Сегменты: (plain|sub|super, content).

    _i _{12} — подстрочный; ^2 ^{n} — надстрочный; \\_ \\^ — литералы.
    После _/^: только цифры ИЛИ только буквы (H_2O → ₂ + O).
    """
    i = 0
    n = len(text)
    buf: list[str] = []

    def flush_plain() -> Iterator[tuple[str, str]]:
        nonlocal buf
        if buf:
            yield ("plain", "".join(buf))
            buf = []

    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in "_^\\":
            buf.append(text[i + 1])
            i += 2
            continue
        if ch in "_^" and i + 1 < n:
            kind = "sub" if ch == "_" else "super"
            nxt = text[i + 1]
            if nxt == "{":
                end = text.find("}", i + 2)
                if end != -1:
                    yield from flush_plain()
                    yield (kind, text[i + 2 : end])
                    i = end + 1
                    continue
            else:
                m = re.match(r"([0-9]+|[A-Za-zА-Яа-яЁё]+)", text[i + 1 :])
                if m:
                    yield from flush_plain()
                    yield (kind, m.group(1))
                    i = i + 1 + m.end()
                    continue
        buf.append(ch)
        i += 1
    yield from flush_plain()


def _escape_plain(text: str) -> str:
    return text.replace("\\", "\\\\").replace("_", "\\_").replace("^", "\\^")


def _encode_script_token(kind: str, content: str) -> str:
    """sub/super → _x / _{…} / ^x / ^{…}."""
    if not content:
        return ""
    mark = "_" if kind == "sub" else "^"
    if re.fullmatch(r"[0-9]+", content) or re.fullmatch(r"[A-Za-zА-Яа-яЁё]+", content):
        return f"{mark}{content}"
    return f"{mark}{{{content}}}"


def merge_script_segments(
    segments: Iterable[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Слить соседние сегменты одного kind."""
    out: list[tuple[str, str]] = []
    for kind, content in segments:
        if not content and kind == "plain":
            continue
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + content)
        else:
            out.append((kind, content))
    return out


def segments_to_markdown(segments: Sequence[tuple[str, str]]) -> str:
    """Обратное к iter_script_segments (для round-trip)."""
    parts: list[str] = []
    for kind, content in merge_script_segments(segments):
        if kind == "plain":
            parts.append(_escape_plain(content))
        elif kind in ("sub", "super"):
            parts.append(_encode_script_token(kind, content))
    return "".join(parts)


def text_roundtrip_scripts(text: str) -> str:
    """parse MD scripts → re-encode (каноническая форма)."""
    return segments_to_markdown(list(iter_script_segments(text)))
