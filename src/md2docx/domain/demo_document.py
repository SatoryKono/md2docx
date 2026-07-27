"""Demo DocumentModel — единый content path для --demo."""

from __future__ import annotations

from md2docx.domain.model import (
    DocumentModel,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Table,
    TitleMeta,
)


def build_demo_model() -> DocumentModel:
    return DocumentModel(
        title=TitleMeta(
            org="МИНИСТЕРСТВО … / ОРГАНИЗАЦИЯ",
            topic="Наименование темы НИР",
            city_year="Город – 2026",
        ),
        blocks=[
            Heading(level=1, text="ВВЕДЕНИЕ", structural=True),
            Paragraph(
                text=(
                    "Текст введения оформляется стилем «Основной текст»: "
                    "выравнивание по ширине, абзацный отступ, интервал 1,5, "
                    "Times New Roman 12 pt."
                )
            ),
            Heading(level=1, text="1 Постановка задачи", structural=False),
            Heading(level=2, text="1.1 Исходные данные", structural=False),
            Paragraph(
                text="Пример абзаца основного текста отчёта о научно-исследовательской работе."
            ),
            ListItem(text="первый пункт", ordered=False),
            ListItem(text="второй пункт", ordered=False),
            Table(
                caption="Таблица 1 — Пример названия таблицы",
                rows=[
                    ["Параметр", "Значение"],
                    ["Поле левое", "30 мм\n(минимум по ГОСТ)"],
                ],
            ),
            Formula(text="E = mc^2"),
            Heading(level=1, text="ЗАКЛЮЧЕНИЕ", structural=True),
            Paragraph(text="Краткое изложение результатов работы."),
            Heading(
                level=1,
                text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
                structural=True,
            ),
            Paragraph(
                text=(
                    "1. ГОСТ 7.32–2017. Отчёт о научно-исследовательской работе. "
                    "Структура и правила оформления. — М., 2017."
                )
            ),
        ],
    )
