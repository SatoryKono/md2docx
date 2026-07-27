# md2docx

**Markdown ↔ DOCX** с оформлением по **ГОСТ 7.32–2017** и стилями, согласованными с эталоном **A.docx**.

| | |
|--|--|
| Версия | **0.2.x** (`md2docx.__version__`) |
| Python | ≥ 3.11 |
| Архитектура | hexagonal (`domain` / `application` / `adapters`) |
| Документация | **[docs/](docs/README.md)** |

## Установка

```bash
pip install -e ".[dev]"   # + pytest, ruff, mypy, coverage
# runtime only:
pip install -e .
```

Зависимости runtime: `python-docx`, `mistune`.

## Быстрый старт (CLI)

```bash
# демо-отчёт
python -m md2docx --demo -o report.docx

# Markdown → DOCX
python -m md2docx -i sample.md -o report.docx \
  --org "ОРГАНИЗАЦИЯ" --topic "Тема НИР" --city-year "Москва – 2026"

# DOCX → Markdown
python -m md2docx -i report.docx -o chapter.md
python -m md2docx -i report.docx -o chapter.md --include-title

# DOCX → DOCX (только стили ГОСТ; ориентация секций сохраняется)
python -m md2docx -i draft.docx -o out.docx --restyle

# строгий режим: нет картинки → exit ≠ 0
python -m md2docx -i sample.md -o out.docx --strict
```

Эквивалент после install: `md2docx -i sample.md -o report.docx`.
Направление задаётся расширениями `-i` / `-o`.

Полный разбор флагов: [docs/user-guide.md](docs/user-guide.md).

## Library API

```python
from md2docx import (
    convert_md_to_docx,
    convert_docx_to_md,
    restyle_docx,
    build_demo_docx,
)

convert_md_to_docx("# ВВЕДЕНИЕ\n\nТекст H_2O.\n", "out.docx")
convert_docx_to_md("out.docx", "out.md")
restyle_docx("draft.docx", "styled.docx")
build_demo_docx("demo.docx")
```

## Возможности

- **MD ↔ DOCX** (канонический round-trip subset, e2e-тесты)
- Заголовки structural / H1–H3 (стили A.docx)
- Списки: маркер **—** + табуляция (без Word auto-bullet)
- Индексы: `H_2O`, `x^2`, `x_{i+1}`
- Таблицы (в т.ч. `<br>` в ячейках), подписи, формулы, цитаты, код
- Секции **portrait / landscape** (`<!-- md2docx:section … -->`)
- Рисунки: ширина = полоса набора секции; restyle не ломает landscape
- Легенды `# – достоверность…` — абзацы, не заголовки
- Поля страницы по умолчанию: **30 / 15 / 20 / 20** mm (лево / право / верх / низ)

Синтаксис: [docs/markdown-features.md](docs/markdown-features.md).
Стили: [docs/styles-a-docx.md](docs/styles-a-docx.md).

### Конфиг стилей

`src/md2docx/config/gost-7.32-2017-styles.json`

```bash
python -m md2docx -i sample.md -o out.docx --config path/to/styles.json
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | успех |
| 1 | runtime / файл не найден / медиа в `--strict` |
| 2 | usage / неподдерживаемый формат / docx→docx без `--restyle` |
| 3 | ошибка style config (зарезервировано) |

## Разработка

```bash
pip install -e ".[dev]"
pytest                                      # unit + integration + e2e
pytest --cov=md2docx --cov-branch --cov-report=term   # ≥ 70%
ruff check src test
mypy src/md2docx/domain src/md2docx/application
```

Подробнее: [docs/development.md](docs/development.md), [docs/architecture.md](docs/architecture.md).

CI: GitHub Actions (`.github/workflows/ci.yml`) — ruff, mypy, pytest + coverage.

## Документация

| Раздел | Ссылка |
|--------|--------|
| Оглавление | [docs/README.md](docs/README.md) |
| Руководство пользователя | [docs/user-guide.md](docs/user-guide.md) |
| Markdown-фичи | [docs/markdown-features.md](docs/markdown-features.md) |
| Архитектура | [docs/architecture.md](docs/architecture.md) |
| Требования (Must/Should) | [docs/architecture-requirements.md](docs/architecture-requirements.md) |
| ADR | [docs/adr/](docs/adr/) |

## Лицензия

MIT (при необходимости уточните в репозитории).
