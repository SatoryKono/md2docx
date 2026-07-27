# Руководство пользователя

## Установка

Требуется **Python ≥ 3.11**.

```bash
git clone <repo>
cd md2docx
pip install -e ".[dev]"   # dev: pytest, ruff, mypy, coverage
# или только runtime:
pip install -e .
```

Точка входа:

```bash
python -m md2docx -h
# после install:
md2docx -h
```

## Быстрый старт

```bash
# демо-отчёт
python -m md2docx --demo -o report.docx

# Markdown → DOCX
python -m md2docx -i sample.md -o report.docx \
  --org "ОРГАНИЗАЦИЯ" --topic "Тема НИР" --city-year "Москва – 2026"

# DOCX → Markdown
python -m md2docx -i report.docx -o chapter.md
python -m md2docx -i report.docx -o chapter.md --include-title   # YAML front matter

# DOCX → DOCX: только стили ГОСТ (контент как есть)
python -m md2docx -i draft.docx -o out.docx --restyle
```

Направление выбирается по **расширениям** `-i` / `-o` (`.md` ↔ `.docx`).

## Library API

```python
from md2docx import (
    convert_md_to_docx,
    convert_docx_to_md,
    restyle_docx,
    build_demo_docx,
)
from md2docx.domain.model import TitleMeta
from md2docx.domain.stylespec import RenderOptions

# MD text или путь к .md
convert_md_to_docx(
    "# ВВЕДЕНИЕ\n\nТекст H_2O.\n",
    "out.docx",
    title=TitleMeta(org="ОРГ", topic="Тема", city_year="Город – 2026"),
)

convert_docx_to_md("out.docx", "out.md", include_title=False, outline=True)
restyle_docx("draft.docx", "styled.docx")
build_demo_docx("demo.docx")
```

Опции оформления: `RenderOptions` (`font`, `body_pt`, `table_pt`, `line_spacing`,
`first_line_mm`, `page`, `page_numbers`, `strict`).  
Конфиг JSON: аргумент `config=` в `convert_md_to_docx` или CLI `--config`.

## CLI: основные флаги

### Ввод / вывод

| Флаг | Назначение |
|------|------------|
| `-i` / `--input` | входной `.md` или `.docx` |
| `-o` / `--output` | выход (если не задан — по умолчанию из имени входа) |
| `--demo` | собрать демо-DOCX |
| `--restyle` | docx→docx: наложить стили ГОСТ |
| `--include-title` | docx→md: YAML front matter (`org`, `topic`, `city_year`) |
| `--no-outline` | docx→md: не отрезать преамбулу/TOC до «1 …» |
| `--media-dir PATH` | docx→md: каталог картинок (по умолчанию `<stem>_media`) |

### Оформление

| Флаг | Назначение |
|------|------------|
| `--config PATH` | JSON-профиль стилей/полей |
| `--font`, `--body-pt`, `--table-pt`, `--line-spacing` | переопределения |
| `--margin-left/right/top/bottom MM` | поля страницы |
| `--no-page-numbers` | без номеров страниц |
| `--strict` | отсутствующие изображения → non-zero exit |
| `-q` / `-v` | quiet / verbose |
| `--list-styles` | список имён стилей |

### Титул (md→docx)

`--org`, `--topic`, `--city-year` — поля титульного листа.

## Exit codes

| Code | Смысл |
|------|--------|
| 0 | успех |
| 1 | runtime / файл не найден / медиа в `--strict` |
| 2 | usage / неподдерживаемый формат / docx→docx без `--restyle` |
| 3 | ошибка style config (зарезервировано) |

## Типичные сценарии

### 1. Отчёт из Markdown

1. Пишете текст в MD (см. [markdown-features.md](markdown-features.md)).
2. `python -m md2docx -i report.md -o report.docx`.
3. При необходимости: `--restyle` после правок в Word **не** нужен, если генерируете заново.

### 2. Извлечение из Word (эталон A.docx)

```bash
python -m md2docx -i A.docx -o chapter.md --no-outline --media-dir A_media
```

- Изображения → `A_media/image_NNN.png`
- Секции с landscape → комментарии `<!-- md2docx:section ... -->`
- Легенды вида `# – достоверность…` остаются **абзацами** (не заголовками)

### 3. Round-trip контроль

```bash
python -m md2docx -i A.docx -o mdA.md --no-outline --media-dir A_media
python -m md2docx -i mdA.md -o docxA.docx
```

Проверяйте таблицы (ячейки с переносами → `<br>`), рисунки (ширина = полоса набора), ориентацию секций.

### 4. Только переоформление существующего DOCX

```bash
python -m md2docx -i draft.docx -o gost.docx --restyle
```

Стили/поля ГОСТ накладываются; **ориентация и размер каждой секции сохраняются**.

## Конфиг стилей

Канонический файл:

`src/md2docx/config/gost-7.32-2017-styles.json`

```bash
python -m md2docx -i sample.md -o out.docx --config path/to/styles.json
```

`--config` задаёт defaults (шрифт, кегль, line spacing, first line), page margins и table pt.  
Карта стилей Word: [styles-a-docx.md](styles-a-docx.md).

## Ограничения round-trip

| Элемент | Поведение |
|---------|-----------|
| Объединённые ячейки Word | только текстовая сетка |
| Рисунки **внутри** ячеек таблицы | не всегда извлекаются как body-Figure |
| Ширины столбцов / сложный layout | не моделируются |
| Полный TOC Word | при чтении фильтруется из body |
| Произвольные Word-стили | маппятся на подмножество ГОСТ/A.docx |
| Легенды `# – …` | в MD экранируются / не парсятся как ATX-heading |

## См. также

- [markdown-features.md](markdown-features.md) — синтаксис
- [architecture.md](architecture.md) — как устроен код
- [development.md](development.md) — тесты и CI
