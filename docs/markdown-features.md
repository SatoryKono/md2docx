# Возможности Markdown ↔ DOCX

Каноническая сериализация: `domain.markdown_serialize.serialize_document`.
Парсеры: `SimpleMarkdownParser` (линейный) / опционально mistune-адаптер.

## Заголовки

| MD | DOCX стиль | Примечание |
|----|------------|------------|
| `# ВВЕДЕНИЕ` | StructuralHeading | keyword structural → CAPS, с новой страницы |
| `# 1 Раздел` | Heading 1 | разрыв страницы |
| `## 1.1 …` | Heading 2 | пустая строка перед |
| `### 1.1.1 …` | Heading 3 | |

Structural keywords: РЕФЕРАТ, СОДЕРЖАНИЕ, ВВЕДЕНИЕ, ЗАКЛЮЧЕНИЕ, СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ, ПРИЛОЖЕНИЕ, …

### Не заголовки

Строки-легенды графиков/таблиц:

```markdown
\# – достоверность различия (P < 0,05) с группой ложной патологии,
```

или без экранирования (парсер распознаёт `# – …` как **Paragraph**).
Символ `#` здесь — маркер легенды, не ATX-heading.

## Индексы

| Синтаксис | Результат |
|-----------|-----------|
| `H_2O` | подстрочная 2 |
| `x^2` | надстрочная 2 |
| `x_{i+1}` | подстрочный блок |
| `a^{n}` | надстрочный блок |
| `\_` `\^` | литералы `_` / `^` |

## Списки

- Ненумерованный (`- item` / `* item`): в DOCX маркер **—** (Em Dash) + **табуляция**, стиль `GostListDash` (без Word numPr).
- Нумерованный (`1. item` / `1) item`): префикс `N) `, стиль `GostListNumber`.

## Таблицы

```markdown
Таблица: Параметры модели

| Колонка A | Колонка B |
| --- | --- |
| значение | line1<br>line2 |
| a\|b | экранированный \| |
```

- Подпись: `Таблица: …` или полный текст, начинающийся с «Таблица».
- Переносы в ячейках: **`<br>`** (сырой `\n` при serialize превращается в `<br>` — иначе GFM table ломается).
- `|` в ячейке: `\|`.
- В DOCX: Table Grid, TableHeader / TableCell, padding ~3 pt.

## Рисунки

```markdown
![Рисунок 1 — Схема](media/fig01.png)

Рисунок: подпись без файла
```

- md→docx: ширина = **полоса набора** текущей секции (`page_width − left − right`).
- Высокие изображения: масштабируются, чтобы высота ≤ полоса − запас под подпись.
- Абзац рисунка: center, firstLine/left/right indent = 0 (не наследует отступ Normal).
- docx→md: media в `--media-dir` (по умолчанию `<stem>_media`), пути в POSIX-форме.

## Формулы

```markdown
$$E = mc^2$$
```

В DOCX: стиль Formula, номер справа `(N)`. При docx→md номер снимается.

## Цитаты и код

```markdown
> цитата
> продолжение

```
код
```
```

## Ориентация / секции

```markdown
<!-- md2docx:section orientation=portrait width_mm=210 height_mm=297 margin_left=30 margin_right=15 margin_top=20 margin_bottom=20 -->

Текст книжной ориентации.

<!-- md2docx:section orientation=landscape width_mm=210 height_mm=297 margin_left=30 margin_right=15 margin_top=20 margin_bottom=20 -->

| широкая | таблица |
| --- | --- |

<!-- md2docx:section orientation=portrait width_mm=210 height_mm=297 margin_left=30 margin_right=15 margin_top=20 margin_bottom=20 -->
```

- docx→md: секции Word с **различающимся** PageSetup → директивы.
- md→docx: `doc.add_section` + `orientation` / size / margins.
- Одинаковые соседние setup могут сливаться (допуск ~0.5 mm).

## Титул (front matter)

docx→md с `--include-title`:

```yaml
---
org: ОРГАНИЗАЦИЯ
topic: Тема
city_year: Москва – 2026
---
```

md→docx: также CLI `--org` / `--topic` / `--city-year`.

## DOCX → Markdown: фильтры

- TOC-строки и служебные стили (Footer, Header, TOC) отбрасываются.
- Outline-режим (по умолчанию): преамбула до body-раздела может пропускаться; `--no-outline` — читать с начала.
- CaptionTable / CaptionFigure → подписи; H4-алиасы → Heading 3.

## E2E

| Тест | Цепочка |
|------|---------|
| `test/e2e/test_md_docx_md_roundtrip.py` | md → docx → md |
| `test/e2e/test_docx_md_docx_roundtrip.py` | docx fragment → md → docx → md |
| `test/e2e/test_orientation_roundtrip.py` | portrait / landscape |
| `test/e2e/test_figure_size.py` | размер рисунков |

Фрагмент эталона:

```bash
python scripts/extract_a_fragment.py A.docx
```

## См. также

- [user-guide.md](user-guide.md) — CLI и сценарии
- [styles-a-docx.md](styles-a-docx.md) — имена стилей Word
