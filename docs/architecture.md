# Архитектура md2docx (hexagonal)

## Цель

Конвертация **Markdown ↔ DOCX** с оформлением по **ГОСТ 7.32–2017** и стилями,
выведенными из эталона `A.docx`. Код разделён по гексагональной архитектуре
(ports & adapters).

## Слои

```
        CLI (inbound adapter)          Library facade
                 │                           │
                 └───────────┬───────────────┘
                             ▼
                  Application use cases
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Domain         Ports         Outbound adapters
        (model, rules)  (Protocol)    (MD / DOCX / JSON)
```

| Пакет | Ответственность | Запрещено |
|-------|-----------------|-----------|
| `md2docx.domain` | DocumentModel, PageSetup, serialize, scripts, structural, StylePack | `docx`, argparse, файловый I/O Word |
| `md2docx.application` | Convert / Restyle / Demo / Facade | детали OOXML |
| `md2docx.adapters.inbound` | CLI (composition root) | бизнес-правила |
| `md2docx.adapters.outbound` | parser/writer MD, reader/writer DOCX, JSON styles | — |

## Структура пакета

```
src/md2docx/
├── domain/
│   ├── model.py              # Block union, DocumentModel, TitleMeta
│   ├── page.py               # PageSetup, section directive parse
│   ├── markdown_serialize.py # model → канонический MD
│   ├── scripts.py / spans.py # индексы _ / ^
│   ├── structural.py         # keywords structural headings
│   ├── stylespec.py          # RenderOptions, StylePack, defaults
│   ├── list_markers.py
│   ├── demo_document.py      # модель демо-отчёта
│   └── errors.py
├── application/
│   ├── ports.py              # единственный реестр Protocol
│   ├── convert_md.py / convert_docx.py / restyle.py / demo.py
│   └── facade.py             # public library API
└── adapters/
    ├── inbound/cli.py
    └── outbound/
        ├── markdown_parser.py / mistune_parser.py / markdown_writer.py
        ├── docx_reader.py / docx_writer.py
        ├── json_style_repo.py
        ├── docx_engine.py    # facade re-export
        └── docx/             # styles, page, runs, cells, restyle, demo helpers
```

## Use cases

| Use case | Вход | Выход |
|----------|------|--------|
| **ConvertMarkdownToDocx** | MD text + RenderOptions | `.docx` |
| **ConvertDocxToMarkdown** | `.docx` | канонический `.md` (+ media) |
| **RestyleDocx** | `.docx` | `.docx` (стили ГОСТ; секции page setup сохраняются) |
| **BuildDemo** | — | демо-DOCX из `build_demo_model()` |

## Порты (`application/ports.py`)

- `MarkdownParser.parse(text) → Sequence[Block]`
- `DocxReader.read(path) → DocumentModel`
- `MarkdownWriter.write(model, dest, *, include_title) → Path`
- `DocumentWriter.write(model, options, dest) → Path`
- `DocumentRestyler.restyle(source, dest, options) → Path`
- `StyleRepository.load(path?) → StylePack`

## Ключевые инварианты

1. **Семантика страницы** — `PageSetup` / `SectionBreak` в domain; Word orientation/size/margins — только в adapters.
2. **Канонический MD** — `serialize_document`; round-trip e2e сверяет стабильный текст.
3. **Рисунки** — ширина = `page_width − margins` текущей секции; firstLine indent абзаца картинки = 0; высокие — cap по высоте полосы.
4. **Restyle** — не сбрасывает landscape-секции (save/restore PageSetup).
5. **Легенды `# – …`** — Paragraph, не Heading (escape `\#` + эвристика парсера).

## Round-trip

```
md ──parse──► model ──write──► docx ──read──► model ──serialize──► md'
```

Тесты: `test/e2e/`.

## Зависимости слоёв

- domain → stdlib / typing only (без python-docx)
- application → domain + Protocol
- adapters → domain + python-docx / mistune / json / pathlib
- composition: `cli.py`, `facade.py`

## Связанные документы

- [architecture-requirements.md](architecture-requirements.md) — Must/Should
- [adr/0001-hexagonal.md](adr/0001-hexagonal.md)
- [adr/0002-domain-presentation-boundary.md](adr/0002-domain-presentation-boundary.md)
- [plan-hexagonal-refactoring.md](plan-hexagonal-refactoring.md) — история миграции
- [development.md](development.md) — практика разработки
