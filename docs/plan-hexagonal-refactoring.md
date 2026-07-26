# План рефакторинга: hexagonal architecture

Сохранено: 2026-07-26. Источник — согласованный план рефакторинга md2docx.

## Целевая структура

```
md2docx/
├── pyproject.toml
├── README.md
├── sample.md
├── src/md2docx/
│   ├── domain/          # model, stylespec, scripts, structural, list_markers
│   ├── application/     # ports, convert_md, restyle, demo
│   ├── adapters/
│   │   ├── inbound/     # cli
│   │   └── outbound/    # markdown_parser, docx_*, json_style_repo
│   └── config/          # gost-7.32-2017-styles.json
├── test/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── docs/
```

## Этапы

| # | Содержание | Критерий |
|---|------------|----------|
| 0 | Каркас src/test/docs, pyproject, entrypoint | `python -m md2docx -h` |
| 1 | Domain + unit tests (scripts, structural) | pytest unit без docx |
| 2 | MarkdownParser → Blocks | snapshot fixtures |
| 3 | Docx writer/styles/cells | integration convert sample |
| 4 | Application use cases + CLI cutover | полный CLI UX |
| 5 | Docs cleanup, deprecate monolith | shim или удаление |

## Правила

1. Domain без `python-docx`  
2. Списки: `GostListDash` / `GostListNumber`, маркер `—\t`, без `numPr`  
3. StylePack: JSON primary, код — fallback  
4. A.docx (крупный эталон) не коммитить в git  

## Definition of Done

- [x] Каркас hexagonal  
- [x] Domain без docx  
- [x] Use cases + adapters  
- [x] CLI `-i/-o/--demo/--restyle`  
- [x] Тесты unit/integration  
- [x] Документация в docs/  
- [x] Репозиторий GitHub  
