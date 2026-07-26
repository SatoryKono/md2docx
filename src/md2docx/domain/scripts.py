"""Подстрочные (_) и надстрочные (^) индексы — чистая логика без python-docx."""

from __future__ import annotations

import re
from collections.abc import Iterator


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
