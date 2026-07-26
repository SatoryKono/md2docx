# Архитектура md2docx (hexagonal)

## Цель

Конвертация Markdown → DOCX с оформлением по ГОСТ 7.32–2017 и стилями,
выведенными из эталона `A.docx`. Код разделён по гексагональной архитектуре.

## Слои

```
CLI (inbound adapter)
        │
        ▼
Application use cases  ──►  Ports (protocols)
        │                        │
        ▼                        ▼
     Domain              Outbound adapters
  (model, rules)         (MD parser, python-docx, JSON)
```

| Пакет | Ответственность | Запрещено |
|-------|-----------------|-----------|
| `md2docx.domain` | модель документа, индексы `_`/`^`, structural keywords, StylePack | `docx`, `argparse`, I/O |
| `md2docx.application` | сценарии Convert / Restyle / Demo | детали Word XML |
| `md2docx.adapters.inbound` | CLI | бизнес-правила |
| `md2docx.adapters.outbound` | MD→blocks, DOCX writer, стили, JSON | — |

## Структура репозитория

```
src/md2docx/     — пакет
test/            — unit + integration
docs/            — архитектура, ADR, markdown-фичи, стили
```

## Use cases

1. **ConvertMarkdownToDocx** — parse MD → DocumentModel → write DOCX  
2. **RestyleDocx** — наложить StylePack на существующий DOCX  
3. **BuildDemo** — демо-отчёт  

## Порты

- `MarkdownParser.parse(text) -> Sequence[Block]`
- `StyleRepository.load(path?) -> StylePack`
- `DocumentWriter.write(model, options, dest) -> Path`
- `DocumentWriter.restyle(source, dest, options) -> Path`

## Зависимости

- domain → ничего внешнего  
- application → domain + Protocol  
- adapters → domain + python-docx / json / pathlib  
- composition root: `adapters.inbound.cli`

## Этапы внедрения

См. [plan-hexagonal-refactoring.md](plan-hexagonal-refactoring.md) и [adr/0001-hexagonal.md](adr/0001-hexagonal.md).
