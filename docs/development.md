# Разработка

## Структура репозитория

```
md2docx/
├── src/md2docx/           # пакет (hexagonal)
│   ├── domain/            # модель, page, serialize, scripts — без I/O Word
│   ├── application/       # use cases + ports + facade (library API)
│   ├── adapters/
│   │   ├── inbound/cli.py # composition root
│   │   └── outbound/      # MD parser/writer, DOCX reader/writer, styles
│   │       └── docx/      # styles, page, runs, cells, restyle, demo helpers
│   └── config/            # gost-7.32-2017-styles.json
├── test/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── scripts/               # audit, extract fragment
├── docs/
├── sample.md
└── pyproject.toml
```

## Окружение

```bash
pip install -e ".[dev]"
```

Dev-зависимости: `pytest`, `pytest-cov`, `ruff`, `mypy`.  
Runtime: `python-docx`, `mistune`.

## Тесты

```bash
pytest                         # unit + integration + e2e
pytest test/unit -q
pytest test/e2e -q
pytest --cov=md2docx --cov-branch --cov-report=term
```

Пороги (см. `pyproject.toml`):

- **coverage fail_under = 70** (line + branch)
- `omit`: `*/__main__.py`

### Что покрывают e2e

| Файл | Цепочка |
|------|---------|
| `test_md_docx_md_roundtrip.py` | md → docx → md |
| `test_docx_md_docx_roundtrip.py` | docx fragment → md → docx → md |
| `test_orientation_roundtrip.py` | portrait / landscape |
| `test_figure_size.py` | ширина рисунка = text width; indent; height cap |
| `test_a_docx_quality.py` | качество чтения A.docx (если есть локально) |

Фикстура фрагмента A:

```bash
python scripts/extract_a_fragment.py A.docx
# → test/fixtures/a_fragment.docx (+ expected md при наличии)
```

`A.docx` в корне — **локальный эталон** (в `.gitignore`), для CI не обязателен.

## Линтеры / типы

```bash
ruff check src test
mypy src/md2docx/domain src/md2docx/application
```

## CI

`.github/workflows/ci.yml`:

- Python 3.11, 3.12
- ruff → mypy (domain + application) → pytest + coverage

## Library API (для встраивания)

Composition root для библиотек: `md2docx.application.facade`  
(реэкспорт из `md2docx`):

- `convert_md_to_docx`
- `convert_docx_to_md`
- `restyle_docx`
- `build_demo_docx`

CLI composition root: `md2docx.adapters.inbound.cli:main`.

## Полезные скрипты

```bash
# аудит DOCX→MD (метрики / эвристики)
python scripts/audit_docx_md.py A.docx -o report.md --media-dir A_media --no-outline

# фрагмент A для e2e
python scripts/extract_a_fragment.py A.docx
```

## Соглашения

1. **Domain** не импортирует `docx` / argparse / pathlib I/O к Word.
2. Новые порты — только в `application/ports.py`.
3. Стили Word — имена (не style_id) через `_get_style_by_name`.
4. Round-trip MD: переносы в ячейках → `<br>`; абзацы `# – …` не как ATX-heading.
5. Документацию обновлять вместе с публичным CLI/API.

## Архитектурные документы

- [architecture.md](architecture.md)
- [architecture-requirements.md](architecture-requirements.md)
- [adr/0001-hexagonal.md](adr/0001-hexagonal.md)
- [adr/0002-domain-presentation-boundary.md](adr/0002-domain-presentation-boundary.md)
