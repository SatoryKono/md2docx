# Документация md2docx

Конвертация **Markdown ↔ DOCX** с оформлением по **ГОСТ 7.32–2017** и стилями эталона **A.docx**.

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [../README.md](../README.md) | все | установка, быстрый старт, CLI, library API |
| [user-guide.md](user-guide.md) | пользователи | сценарии, флаги, round-trip, ограничения |
| [markdown-features.md](markdown-features.md) | авторы MD | синтаксис, секции, таблицы, рисунки, индексы |
| [styles-a-docx.md](styles-a-docx.md) | верстальщики | карта стилей A.docx → Word |
| [architecture.md](architecture.md) | разработчики | hexagonal-слои, порты, use cases |
| [development.md](development.md) | разработчики | тесты, coverage, CI, скрипты |
| [architecture-requirements.md](architecture-requirements.md) | архитекторы | Must/Should, compliance |
| [adr/](adr/) | архитекторы | ADR (решения) |

## Возможности (кратко)

- **MD → DOCX** и **DOCX → MD** (канонический round-trip subset)
- **Restyle** существующего DOCX стилями ГОСТ (ориентация секций сохраняется)
- Заголовки structural / H1–H3, списки «—» + tab, таблицы, рисунки, формулы
- Индексы `H_2O`, `x^2`, `x_{i+1}`
- Многосекционные документы: portrait / landscape
- Ширина рисунка = полоса набора текущей секции
- Library API: `convert_md_to_docx`, `convert_docx_to_md`, `restyle_docx`, `build_demo_docx`

## Версия пакета

См. `pyproject.toml` / `md2docx.__version__` (текущая ветка: **0.2.x**).
