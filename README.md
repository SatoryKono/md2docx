# md2docx

Конвертация **Markdown → DOCX** с оформлением по **ГОСТ 7.32–2017** и стилями, согласованными с эталоном `A.docx`.

Архитектура: **hexagonal** (`src/md2docx`: domain / application / adapters).  
Документация: [`docs/`](docs/).

## Установка

```bash
pip install -e ".[dev]"
```

## Использование

```bash
python -m md2docx --demo -o report.docx
python -m md2docx -i sample.md -o report.docx --org "ОРГАНИЗАЦИЯ" --topic "Тема" --city-year "Москва – 2026"
python -m md2docx -i draft.docx -o out.docx --restyle
```

Эквивалент: `md2docx -i sample.md -o report.docx`

## Возможности

- Заголовки structural / H1–H3 (стили A.docx `@Header1…4`)
- Списки: маркер **—** + табуляция (без Word-bullet)
- Индексы: `H_2O`, `x^2`, `x_{i+1}`
- Таблицы, подписи, формулы, поля 30/15/20/20 mm

Подробнее: [docs/markdown-features.md](docs/markdown-features.md), [docs/architecture.md](docs/architecture.md).

## Разработка

```bash
pytest
```

## Лицензия

MIT (при необходимости уточните).
