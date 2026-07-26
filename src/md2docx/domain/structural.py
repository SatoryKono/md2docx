"""Структурные заголовки отчёта о НИР (ГОСТ 7.32)."""

STRUCTURAL_KEYWORDS = (
    "РЕФЕРАТ",
    "СОДЕРЖАНИЕ",
    "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
    "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
    "ВВЕДЕНИЕ",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
    "ПРИЛОЖЕНИЕ",
)


def is_structural_heading(text: str) -> bool:
    t = text.strip().upper()
    for kw in STRUCTURAL_KEYWORDS:
        if t == kw or t.startswith(kw + " "):
            return True
    return False
