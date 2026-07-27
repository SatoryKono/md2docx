# Архитектурные требования md2docx

**Статус:** Accepted (каталог требований)  
**Дата:** 2026-07-27  
**Основание:** [ADR 0001](adr/0001-hexagonal.md), [architecture.md](architecture.md), код `src/md2docx`  
**Назначение:** проверяемые инварианты архитектуры. Это **не** sprint-backlog и не design-спека реализации.

Связанный обзор слоёв: [architecture.md](architecture.md).  
План внедрения (исторический): [plan-hexagonal-refactoring.md](plan-hexagonal-refactoring.md).

---

## Как читать документ

| Поле | Смысл |
|------|--------|
| **Must** | Нарушение = дефект архитектуры; блокирует «production-ready» |
| **Should** | Ожидаемый стандарт; отступление только с ADR |
| **Could** | Желательно; не ломает текущую модель |
| **Критерий** | Автоматическая или ручная проверка «да/нет» |
| **Compliance** | `ok` / `partial` / `gap` относительно кода на дату документа |

Требование формулирует **инвариант**, а не задачу («вынести файл X»).

---

## AR-1. Цели и границы системы

### Назначение

CLI-утилита и (в перспективе) библиотека для:

1. **Markdown → DOCX** с оформлением по **ГОСТ 7.32–2017** и стилями, согласованными с эталоном `A.docx`.
2. **DOCX → Markdown** (каноническая сериализация для round-trip subset).
3. **DOCX → DOCX restyle** — наложение пакета стилей ГОСТ/A.docx без смены смыслового контента (насколько позволяет модель).
4. **Demo** — эталонный отчёт для smoke/UX.

### Actors

| Actor | Действие |
|-------|----------|
| Автор отчёта НИР | md → docx |
| Редактор / reverse | docx → md |
| CI / разработчик | pytest, e2e round-trip, demo |
| Интегратор (Could) | вызов use cases без CLI |

### Use cases (приоритет продукта)

| UC | Must/Should/Could |
|----|-------------------|
| ConvertMarkdownToDocx | Must |
| ConvertDocxToMarkdown | Must |
| RestyleDocx | Should |
| BuildDemo | Should |
| Round-trip md↔docx (заявленный subset) | Must |
| Library API без argparse | Could |

### Границы hexagon

| Внутри (core) | Снаружи (adapters / world) |
|---------------|----------------------------|
| `DocumentModel`, правила structural/scripts, serialize | ФС, CLI argv, python-docx, JSON-файлы |
| Use cases + Protocol-порты | Парсинг MD, чтение/запись DOCX, применение стилей OOXML |
| Семантика page/section (`PageSetup`) | Физические twips, Word section XML |

### Non-goals (продукт)

См. также § Non-goals в конце документа.

- Полноценный CommonMark/GFM редактор или preview.
- Сохранение всего Word (OLE, SmartArt, сложные поля, tracked changes).
- WYSIWYG, GUI, серверный multi-tenant SaaS.
- Юридическая «сертификация ГОСТ» как сертификат; цель — практическое соответствие полей/стилей эталону.

### Требования AR-1

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-1.1 | Система предоставляет CLI-режимы md→docx, docx→md, restyle, demo | Must | `python -m md2docx -h` и smoke каждого режима | `adapters.inbound.cli` | Нет основного UX |
| AR-1.2 | Канонический путь данных: **внешний формат → DocumentModel → внешний формат** | Must | Use cases не пишут DOCX минуя model (кроме restyle — см. AR-5.4) | `application/*` | Дубли логики, drift |
| AR-1.3 | Поддерживаемый MD-subset задокументирован | Must | `docs/markdown-features.md` соответствует parser/writer | `docs/`, parsers | Непредсказуемый UX |
| AR-1.4 | Эталон визуальных стилей — A.docx + ГОСТ-поля; A.docx не обязан быть в git | Must | Документ styles; крупный A.docx в `.gitignore` / не в package | `docs/styles*`, repo policy | Раздувание репо |
| AR-1.5 | Out-of-scope возможности не реализуются «тихо» как half-support | Should | Неподдерживаемое → ошибка или явный strip + docs | adapters | Ложная уверенность |

**Compliance AR-1:** AR-1.1 `ok` · AR-1.2 `partial` (demo/restyle обходят model) · AR-1.3 `ok` · AR-1.4 `ok` · AR-1.5 `partial`

---

## AR-2. Архитектурный стиль и слои

### Решение

**Гексагональная архитектура (ports & adapters)** — [ADR 0001](adr/0001-hexagonal.md) (**Accepted**).  
Clean Architecture с лишними DTO/presenter-слоями — **non-goal** (отклонено ADR 0001).

### Слои

```
adapters.inbound (CLI)     ← composition root
        │
        ▼
application (use cases) ──► ports (typing.Protocol)
        │                        │
        ▼                        ▼
     domain              adapters.outbound
  (pure rules)           (MD, DOCX, JSON, FS)
```

### Dependency rule

| От \ К | domain | application | adapters | python-docx / argparse / json I/O |
|--------|--------|-------------|----------|-----------------------------------|
| **domain** | ✅ | ❌ | ❌ | ❌ |
| **application** | ✅ | ✅ (внутри) | ❌ | ❌ (только через Protocol) |
| **adapters** | ✅ | ✅ (вызов UC) | ✅ | ✅ |
| **composition root** | ✅ | ✅ | ✅ | ✅ |

### Требования AR-2

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-2.1 | Пакетная структура: `domain`, `application`, `adapters.inbound`, `adapters.outbound` | Must | Дерево `src/md2docx/` | layout | Потеря границ |
| AR-2.2 | `domain` не импортирует `docx`, `argparse`, не выполняет сетевой I/O | Must | static grep / import-linter | `domain/*` | Не тестируемость |
| AR-2.3 | `application` не импортирует `python-docx` и конкретные adapter-классы | Must | grep imports в `application/` | `application/*` | Слом hexagon |
| AR-2.4 | Use cases зависят от **Protocol**, не от реализаций | Must | конструкторы UC принимают Protocol-типы | `convert_*`, `ports` | Невозможность подмены |
| AR-2.5 | Composition root — единственная сборка адаптеров: `adapters.inbound.cli` (и `__main__`) | Must | Вне CLI нет wiring DocxWriter+Parser (кроме tests) | `cli.py`, tests | Скрытые composition |
| AR-2.6 | Новые внешние интеграции только как outbound/inbound adapters | Must | Review: нет «тихих» вызовов из domain | all | Утечка инфраструктуры |
| AR-2.7 | Should: import-linter или CI-проверка dependency rule | Should | CI job или documented script | CI | Регресс границ |

**Compliance AR-2:** AR-2.1–2.5 `ok` · AR-2.6 `ok` · AR-2.7 `gap`

---

## AR-3. Доменная модель

### Ключевые элементы

| Элемент | Роль |
|---------|------|
| `DocumentModel` | Агрегат: `title`, `default_page`, `blocks` |
| `TitleMeta` | Титул (org, topic, city_year) |
| `Block` union | Heading, Paragraph, ListItem, Table, Figure, Formula, Quote, CodeLine, EmptyLine, SectionBreak |
| `PageSetup` | Ориентация, размер, поля (mm) — **семантика страницы** |
| `is_structural_heading` | Правила ГОСТ-структуры отчёта |
| `iter_script_segments` / reverse | Индексы `_` / `^` |
| `serialize_document` | Канонический MD (domain-level pure function) |
| `RenderOptions` | Параметры оформления для writer (граничный VO) |

### Инварианты модели

1. `Heading.level` ∈ 1..3 (parser clamp).
2. Structural H1 → текст в UPPER (parser/domain rule).
3. Списки — последовательность `ListItem`, без Word `numPr` в модели.
4. `SectionBreak.setup` задаёт page setup для последующих блоков до следующего break.
5. Round-trip scripts: parse → encode сохраняет семантику subset.

### Что не входит в domain

- OOXML, `w:`, python-docx API.
- argparse / пути CLI.
- Применение стилей к `Document` Word.
- Чтение/запись файлов (кроме как данные `str`/`Path` на границе use case).

### Требования AR-3

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-3.1 | Документ представляется `DocumentModel` + `Block` union | Must | model.py; UC работают с model | `domain.model` | Нет единой модели |
| AR-3.2 | Правила structural headings — pure domain | Must | unit tests без docx | `structural.py` | Дубли в writer |
| AR-3.3 | Правила sub/super — pure domain + round-trip helpers | Must | `test_scripts` | `scripts.py` | Потеря индексов |
| AR-3.4 | Канонический MD — детерминированная pure-функция от model | Must | serialize unit + e2e | `markdown_serialize` | Нестабильный RT |
| AR-3.5 | Page/section семантика в domain (`PageSetup`, `SectionBreak`), без OOXML | Must | `page.py` unit; reader/writer map | `page.py`, model | Непереносимость |
| AR-3.6 | Domain **не** содержит обязательных Word style names / twips как API модели | Should | twips/style ids только в adapters **или** ADR exception | `list_markers`, `stylespec` | Утечка Word в core |
| AR-3.7 | Inline rich text (bold/italic/link) — не Must текущего scope; plain + scripts | Could | docs; strip_md_inline поведение задокументировано | parser, model | — |

> **Proposed ADR (если AR-3.6 станет Must):** вынести twips и имена стилей Word из `domain.list_markers` / `domain.stylespec` в outbound mapping.  
> **Сейчас:** AR-3.6 = Should; as-is = `partial` (константы twips/style names в domain).  
> **Не противоречит ADR 0001** (дух pure domain), уточняет границу presentation.

**Compliance AR-3:** AR-3.1–3.5 `ok` · AR-3.6 `partial` · AR-3.7 `ok` (как Could/ограничение)

---

## AR-4. Порты и адаптеры

### Порты (контракты)

| Port | Направление | Методы | Реализация (as-is) |
|------|-------------|--------|-------------------|
| `MarkdownParser` | driven | `parse(text) → Sequence[Block]` | `SimpleMarkdownParser` |
| `DocumentWriter` | driven | `write`, `restyle`, `write_demo` | `DocxWriter` (+ engine) |
| `DocxReader` | driven | `read(path) → DocumentModel` | `DocxReader` |
| `MarkdownWriter` | driven | `write(model, dest, include_title=…)` | `MarkdownWriter` |
| `StyleRepository` | driven | `load(path?) → StylePack` | **нет** (документировалось как план) |

Inbound: CLI (`main`) — driving adapter.

### Правила портов

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-4.1 | Все внешние I/O use cases идут через Protocol в `application/ports.py` | Must | UC imports only ports + domain | `ports.py`, UC | Жёсткая связность |
| AR-4.2 | Единый реестр Protocol: **только** `ports.py` (без дублей в UC-модулях) | Must | нет `*Port(Protocol)` вне ports | `convert_docx.py` | Расхождение контрактов |
| AR-4.3 | Порт описывает **роль**, не библиотеку (`DocumentWriter`, не `PythonDocx`) | Must | имена Protocol | `ports.py` | Ложная абстракция |
| AR-4.4 | ISP: use case зависит только от нужных методов порта | Should | ConvertMd не требует restyle/demo | `DocumentWriter` | Толстые фейки |
| AR-4.5 | Outbound adapters могут использовать python-docx; domain — нет | Must | grep | outbound, domain | — |
| AR-4.6 | Подмена адаптера в тестах возможна без patch internals engine | Should | UC unit с fake writer/parser | tests | Хрупкие тесты |
| AR-4.7 | Style pack loading — через порт `StyleRepository` (когда styles JSON primary) | Should | port + adapter + wiring | planned | Hardcoded styles only |
| AR-4.8 | Адаптеры не содержат продуктовых use-case веток «if mode==…» уровня CLI | Should | CLI routing vs writer | cli vs writer | Размытие слоёв |

> **Proposed ADR (AR-4.4 / split DocumentWriter):** разделить `DocumentWriter` / `DocumentRestyler` / demo-via-model, если ISP станет Must.  
> Согласуется с ADR 0001; меняет только форму портов.

**Compliance AR-4:** AR-4.1 `ok` · AR-4.2 `ok` (единый `ports.py`, 2026-07-27) · AR-4.3 `ok` · AR-4.4 `partial` · AR-4.5 `ok` · AR-4.6 `partial` · AR-4.7 `gap` · AR-4.8 `ok`

---

## AR-5. Use cases (application)

| Use case | Оркестрация | Side effects |
|----------|-------------|--------------|
| `ConvertMarkdownToDocx` | parse → `DocumentModel` → `write` | создаёт `.docx` |
| `ConvertDocxToMarkdown` | `read` → `write` md | создаёт `.md` |
| `RestyleDocx` | `restyle(source, dest, options)` | создаёт/перезаписывает `.docx` |
| `BuildDemo` | `write_demo` | создаёт demo `.docx` |

### Требования AR-5

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-5.1 | Application-слой тонкий: оркестрация портов, без Word XML | Must | нет `from docx` в application | `application/*` | Утечка инфраструктуры |
| AR-5.2 | Convert MD: единственный путь записи контента — `DocumentWriter.write(model, …)` | Must | `convert_md.py` | convert_md | Параллельные pipeline |
| AR-5.3 | Convert DOCX→MD: `DocxReader` + `MarkdownWriter` only | Must | `convert_docx.py` | convert_docx | — |
| AR-5.4 | Restyle **может** не строить полный `DocumentModel` (ограничение scope); обязан идти через порт, не CLI→engine | Must | `RestyleDocx` → port | restyle | Обход слоёв |
| AR-5.5 | Demo **Should** строиться как `DocumentModel` + `write` (единый render path) | Should | нет отдельного content-pipeline | demo, engine | Дубли рендера |
| AR-5.6 | Use case не парсит argparse и не печатает в stdout | Must | I/O UX только в CLI | application vs cli | Смешение UI |
| AR-5.7 | Опции оформления передаются явным `RenderOptions` (или StylePack), не global mutable state | Must | нет module-level mutate options | stylespec, UC | Гонки/скрытое состояние |

**Compliance AR-5:** AR-5.1–5.4 `ok` · AR-5.5 `gap` · AR-5.6 `ok` · AR-5.7 `ok`

---

## AR-6. Качество и ограничения (quality attributes)

| ID | Атрибут | Текст требования | P | Метрика / проверка | Модули | Риск |
|----|---------|------------------|---|-------------------|--------|------|
| AR-6.1 | Testability | Domain и serialize тестируются без python-docx | Must | unit green без Document() | domain, test/unit | — |
| AR-6.2 | Maintainability | Outbound DOCX-логика модульна; один файл не «бог»-модуль без границ | Should | rational split; review size | `docx_engine` | Стоимость изменений |
| AR-6.3 | Correctness (ГОСТ/styles) | Поля страницы default 30/15/20/20 mm; списки без Word bullets (`numPr` отсутствует) | Must | integration asserts | writer, engine | Несоответствие отчёта |
| AR-6.4 | Correctness (scripts) | Sub/super subset сохраняется md→docx и в round-trip MD | Must | unit + e2e | scripts, writer, reader | Потеря формул |
| AR-6.5 | Round-trip | Для **заявленного subset** `serialize(parse(…))` и e2e md→docx→md стабильны | Must | `test/e2e/*roundtrip*` | serialize, reader, writer | Потеря данных |
| AR-6.6 | Extensibility | Новый тип Block = model + parser + serialize + writer (+ reader) | Should | checklist в docs | model, adapters | Забытые ветки |
| AR-6.7 | Performance | Документы типичного отчёта НИР (порядка ≤200 стр. / разумный MD) конвертируются без спец. стриминга | Could | manual/CI timeout smoke | all | — |
| AR-6.8 | CLI UX | Понятные сообщения об ошибках; `--verbose` → traceback; quiet mode | Should | CLI tests | cli | Плохой DX |
| AR-6.9 | Security | Только локальные файлы; нет выполнения содержимого MD | Must | code review; no eval | all | RCE/path issues |
| AR-6.10 | Determinism | serialize_document детерминирован на одной версии | Must | повторный serialize identical | markdown_serialize | Flaky RT |

**Compliance AR-6:** 6.1 `ok` · 6.2 `partial` · 6.3 `ok` · 6.4 `ok` · 6.5 `ok` · 6.6 `partial` · 6.7 `ok` (не измерено) · 6.8 `partial` · 6.9 `ok` · 6.10 `ok`

---

## AR-7. Конфигурация и стили

### Политика

```
CLI flags  >  --config JSON  >  code defaults (stylespec / engine)
```

Package-data: `src/md2docx/config/gost-7.32-2017-styles.json` — канонический артефакт описания стилей (документация + future primary).

### Требования AR-7

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-7.1 | Default page margins ГОСТ: left 30, right 15, top 20, bottom 20 (mm) | Must | defaults + integration | stylespec, page, engine | Неверный отчёт |
| AR-7.2 | Единственный committed source of truth для JSON-описания стилей (без тихого дубля) | Must | один канонический path в package | `config/` | Drift JSON |
| AR-7.3 | Override: CLI > config file > defaults | Must | documented + tests | cli `_options_from_args` | Непредсказуемость |
| AR-7.4 | `--config` влияет на применяемые параметры (как минимум page/font/body); **Should** — полные paragraph styles из JSON | Should / Could full | load tests | cli, engine | JSON «для галочки» |
| AR-7.5 | Style application живёт в outbound adapter, не в domain rules | Must | apply_* only in adapters | engine | — |
| AR-7.6 | Списки: маркер U+2014 + TAB; без `numPr` | Must | integration test | list_markers, writer | Word bullets |
| AR-7.7 | Schema JSON версионируется / документируется при breaking change | Should | notes в JSON или docs | config, docs | Ломающий конфиг |

> **Proposed ADR (styles JSON primary):** StylePack + StyleRepository как Must implementation.  
> Пока AR-7.4 full styles = Should; as-is partial (частичный parse config).

**Compliance AR-7:** 7.1 `ok` · 7.2 `partial` (возможны дубли в корне) · 7.3 `ok` · 7.4 `partial` · 7.5 `ok` · 7.6 `ok` · 7.7 `partial`

---

## AR-8. Ошибки и наблюдаемость

### Требования AR-8

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-8.1 | Ошибки пользователя → stderr + non-zero exit; success path → 0 | Must | CLI behavior | cli | Автоматизация ломается |
| AR-8.2 | Задокументированы exit codes (минимум: 0 ok, 1 runtime/not found, 2 usage/unsupported) | Should | README или architecture | cli, docs | — |
| AR-8.3 | `--verbose` включает traceback | Must | CLI | cli | Невозможна отладка |
| AR-8.4 | Запрещён silent `except: pass` на потере контента (изображения, таблицы) без warning | Must | grep + policy `--strict` Should | writer, reader | Тихая порча |
| AR-8.5 | Типизированная иерархия ошибок application/domain (не голый `Exception` в UC) | Should | `Md2DocxError` tree | errors module | Неточный mapping |
| AR-8.6 | Не логировать секреты; пути файлов можно | Should | review | cli | — |

**Compliance AR-8:** 8.1 `ok` · 8.2 `ok` (README exit codes) · 8.3 `ok` · 8.4 `ok` (warning + `--strict`/`MediaError`) · 8.5 `partial` (`Md2DocxError` hierarchy) · 8.6 `ok`

---

## AR-9. Тестовая стратегия (как архитектурное требование)

### Пирамида

| Уровень | Что | Must/Should |
|---------|-----|-------------|
| Unit domain | structural, scripts, page, serialize | Must |
| Unit adapters (лёгкие) | parser fixtures, reader filters | Should |
| Integration | md→docx asserts styles/lists/scripts | Must |
| E2E round-trip | md→docx→md; orientation; docx fragment | Must |
| CLI contract | exit codes, routing | Should |
| Golden style properties | margins, no numPr, heading styles | Should |

### Требования AR-9

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-9.1 | `pytest` — основной test runner; `test/` layout unit/integration/e2e | Must | pyproject + tree | test/, pyproject | — |
| AR-9.2 | Domain unit не требуют установленного Word | Must | CI linux/windows python only | test/unit | — |
| AR-9.3 | Есть e2e round-trip на заявленный subset | Must | test/e2e green | e2e | Регресс RT |
| AR-9.4 | Критичные инварианты ГОСТ-списков/индексов покрыты | Must | integration | test/integration | — |
| AR-9.5 | Новые Block types без тестов parser+serialize+writer — дефект | Should | review checklist | — | Дыры RT |
| AR-9.6 | CI запускает pytest на PR/push | Should | GitHub Actions | `.github/` | Слепые регрессии |
| AR-9.7 | Не коммитить огромные бинарные эталоны без нужды; fragment fixtures ok | Must | repo size policy | fixtures | — |

**Compliance AR-9:** 9.1–9.4 `ok` · 9.5 `partial` · 9.6 `ok` (GitHub Actions CI) · 9.7 `ok`

---

## AR-10. Эволюция и совместимость

### Public surface

| Surface | Статус |
|---------|--------|
| CLI `md2docx` / `python -m md2docx` | **Must** public |
| Package import use cases / domain | de-facto; **Should** стабилизировать |
| `gost_styles_python_docx` shim | deprecated; removable on major |
| Library facade API | Could |

### Требования AR-10

| ID | Текст требования | P | Критерий проверки | Модули | Риск при нарушении |
|----|------------------|---|-------------------|--------|--------------------|
| AR-10.1 | Breaking changes CLI flags / exit codes — semver minor/major + CHANGELOG | Should | release notes | README | Ломание скриптов |
| AR-10.2 | Архитектурные решения фиксируются ADR; ADR 0001 — база | Must | `docs/adr/` | docs | Повтор монолита |
| AR-10.3 | Изменение dependency rule или отказ от hexagonal → новый ADR (не молча) | Must | review | docs | — |
| AR-10.4 | Deprecated shim предупреждает и делегирует в CLI | Should | DeprecationWarning | root shim | — |
| AR-10.5 | Docs (architecture, requirements, markdown-features) не противоречат коду | Must | review / audit | docs | Drift |
| AR-10.6 | Расширение форматов (например HTML) — только новый adapter + port, без ломки domain | Could | design | adapters | — |

**Compliance AR-10:** 10.1 `partial` · 10.2 `ok` · 10.3 `ok` · 10.4 `ok` · 10.5 `partial` · 10.6 n/a

---

## Сводная матрица compliance (as-is)

| ID | P | Status | Комментарий |
|----|---|--------|-------------|
| AR-1.1 | Must | **ok** | CLI режимы есть |
| AR-1.2 | Must | **partial** | demo/restyle не через полный model path |
| AR-1.3 | Must | **ok** | markdown-features |
| AR-1.4 | Must | **ok** | A.docx policy |
| AR-1.5 | Should | **ok** | warning + `--strict` (P0.2) |
| AR-2.1–2.5 | Must | **ok** | hexagonal layout |
| AR-2.7 | Should | **gap** | нет import-linter/CI boundaries |
| AR-3.1–3.5 | Must | **ok** | model/page/scripts/serialize |
| AR-3.6 | Should | **partial** | twips/style names в domain |
| AR-4.1 | Must | **ok** | |
| AR-4.2 | Must | **ok** | ports unified |
| AR-4.4 | Should | **partial** | толстый DocumentWriter |
| AR-4.6 | Should | **partial** | мало fake-port unit |
| AR-4.7 | Should | **gap** | StyleRepository отсутствует |
| AR-5.1–5.4, 5.6–5.7 | Must | **ok** | |
| AR-5.5 | Should | **gap** | write_demo отдельный path |
| AR-6.1, 6.3–6.5, 6.9–6.10 | Must | **ok** | |
| AR-6.2 | Should | **partial** | docx_engine ~1108 LOC |
| AR-6.8 | Should | **ok** | README exit codes |
| AR-7.1, 7.3, 7.5–7.6 | Must | **ok** | |
| AR-7.2 | Must | **ok** | package config only |
| AR-7.4 | Should | **partial** | JSON не primary styles |
| AR-8.1, 8.3, 8.4 | Must | **ok** | warning + `--strict` |
| AR-8.2 | Should | **ok** | documented codes |
| AR-8.5 | Should | **partial** | `Md2DocxError` hierarchy |
| AR-9.1–9.4, 9.6–9.7 | Must/Should | **ok** | CI + e2e |
| AR-10.2–10.4 | Must/Should | **ok** | ADR 0001 |
| AR-10.5 | Must | **partial** | StylePack marked planned |

### Сводка

| Status | Must | Should+Could (учёт Must-first) |
|--------|------|--------------------------------|
| ok | hexagon, ports unify, media strict, CI, round-trip, JSON SoT path | exit codes docs |
| partial | error mapping end-to-end, engine modularity (~1108 LOC), golden styles, domain twips | ISP, config depth styles |
| gap | StyleRepository, demo-via-model, library facade, mypy/coverage | second writer / rich inline |

**Оценка зрелости архитектуры (требования):** foundation **ok**, production hardening **partial**.  
**Backlog sync:** GitHub epic #1 (issues актуализированы под as-is).

---

## Матрица трассировки (use case → ports → adapters → tests)

| Use case | Ports | Adapters | Tests (as-is) |
|----------|-------|----------|---------------|
| ConvertMarkdownToDocx | MarkdownParser, DocumentWriter | SimpleMarkdownParser, DocxWriter | unit parser; integration convert; e2e md→docx→md |
| ConvertDocxToMarkdown | DocxReader, MarkdownWriter | DocxReader, MarkdownWriter | unit reader filters; e2e docx fragment / orientation |
| RestyleDocx | DocumentWriter.restyle | DocxWriter → engine.restyle | **thin / gap** dedicated tests |
| BuildDemo | DocumentWriter.write_demo | engine.build_demo | CLI smoke; **gap** unit model path |
| serialize (support) | — pure domain | — | unit serialize + scripts; e2e RT |
| Styles config | (future StyleRepository) | CLI json.loads partial | **gap** full StylePack |

---

## Non-goals (архитектура)

1. Не вводить Clean Architecture с отдельными DTO/presenter/controller слоями сверх hexagon (ADR 0001).
2. Не требовать 100% fidelity произвольного DOCX Word.
3. Не делать domain «Word-free» ценой потери shippable MVP **без** ADR (AR-3.6 остаётся Should до ADR).
4. Не фиксировать конкретный MD-движок (custom vs mistune) как Must — только контракт `MarkdownParser`.
5. Не включать GUI, server API, cloud sync в архитектуру v0.
6. Не коммитить полный `A.docx` как package data.
7. Не подменять этот документ списком GitHub issues (issues — реализация; здесь — инварианты).

---

## Согласование с ADR 0001

| Тема | ADR 0001 | Эти требования |
|------|----------|----------------|
| Hexagonal | Accepted | AR-2 подтверждает |
| domain pure | Yes | AR-2.2, AR-3; AR-3.6 уточняет presentation leak как Should |
| application + ports | Yes | AR-4, AR-5 |
| adapters CLI/MD/DOCX | Yes | + DocxReader/MarkdownWriter (эволюция, совместима) |
| Отказ от excess Clean layers | Yes | Non-goal #1 |
| StyleRepository / ISP split / error model | не специфицированы | Should/Proposed ADR — **не отменяют** 0001 |

### Proposed ADR topics (не созданы; маркеры для будущего)

| Тема | Связанные AR | Зачем отдельный ADR |
|------|--------------|---------------------|
| StylePack + StyleRepository JSON-primary | AR-4.7, AR-7.4 | меняет source of truth стилей |
| Split DocumentWriter (ISP) + demo via model | AR-4.4, AR-5.5 | меняет форму портов |
| Domain presentation purification (no twips) | AR-3.6 | ужесточает pure domain |
| Typed error model + exit codes | AR-8 | контракт CLI |

---

## Полный каталог (компактная таблица)

| ID | P | Кратко | Status |
|----|---|--------|--------|
| AR-1.1 | Must | CLI режимы | ok |
| AR-1.2 | Must | model-centric pipeline | partial |
| AR-1.3 | Must | MD subset documented | ok |
| AR-1.4 | Must | A.docx policy | ok |
| AR-1.5 | Should | no silent half-support | partial |
| AR-2.1 | Must | package layers | ok |
| AR-2.2 | Must | domain no docx/I/O | ok |
| AR-2.3 | Must | application no docx | ok |
| AR-2.4 | Must | UC → Protocol | ok |
| AR-2.5 | Must | composition root CLI | ok |
| AR-2.6 | Must | integrations as adapters | ok |
| AR-2.7 | Should | CI dependency rule | gap |
| AR-3.1 | Must | DocumentModel | ok |
| AR-3.2 | Must | structural pure | ok |
| AR-3.3 | Must | scripts pure | ok |
| AR-3.4 | Must | serialize pure | ok |
| AR-3.5 | Must | PageSetup semantic | ok |
| AR-3.6 | Should | no twips API in domain | partial |
| AR-3.7 | Could | rich inline | n/a scope |
| AR-4.1 | Must | I/O via ports | ok |
| AR-4.2 | Must | single ports.py | ok |
| AR-4.3 | Must | role-named ports | ok |
| AR-4.4 | Should | ISP | partial |
| AR-4.5 | Must | docx only outbound | ok |
| AR-4.6 | Should | fake adapters in tests | partial |
| AR-4.7 | Should | StyleRepository | gap |
| AR-4.8 | Should | no UC logic in adapters | ok |
| AR-5.1 | Must | thin application | ok |
| AR-5.2 | Must | convert md → write(model) | ok |
| AR-5.3 | Must | convert docx ports | ok |
| AR-5.4 | Must | restyle via port | ok |
| AR-5.5 | Should | demo via model | gap |
| AR-5.6 | Must | no argparse in UC | ok |
| AR-5.7 | Must | explicit RenderOptions | ok |
| AR-6.1 | Must | domain testable | ok |
| AR-6.2 | Should | modular docx outbound | partial |
| AR-6.3 | Must | ГОСТ margins / no numPr | ok |
| AR-6.4 | Must | scripts correctness | ok |
| AR-6.5 | Must | round-trip subset | ok |
| AR-6.6 | Should | Block extension path | partial |
| AR-6.7 | Could | typical report perf | ok |
| AR-6.8 | Should | CLI UX errors | ok |
| AR-6.9 | Must | local files only | ok |
| AR-6.10 | Must | deterministic serialize | ok |
| AR-7.1 | Must | default margins | ok |
| AR-7.2 | Must | single JSON SoT | ok |
| AR-7.3 | Must | override precedence | ok |
| AR-7.4 | Should | config applies styles | partial |
| AR-7.5 | Must | styles in adapter | ok |
| AR-7.6 | Must | list marker rules | ok |
| AR-7.7 | Should | config schema docs | partial |
| AR-8.1 | Must | stderr + exit codes | ok |
| AR-8.2 | Should | documented codes | ok |
| AR-8.3 | Must | --verbose traceback | ok |
| AR-8.4 | Must | no silent content loss | ok |
| AR-8.5 | Should | typed errors | partial |
| AR-8.6 | Should | no secrets in logs | ok |
| AR-9.1 | Must | pytest layout | ok |
| AR-9.2 | Must | domain unit w/o Word | ok |
| AR-9.3 | Must | e2e round-trip | ok |
| AR-9.4 | Must | list/script integration | ok |
| AR-9.5 | Should | tests for new blocks | partial |
| AR-9.6 | Should | CI pytest | ok |
| AR-9.7 | Must | no huge binaries policy | ok |
| AR-10.1 | Should | semver CLI | partial |
| AR-10.2 | Must | ADR process | ok |
| AR-10.3 | Must | hexagonal change via ADR | ok |
| AR-10.4 | Should | deprecated shim | ok |
| AR-10.5 | Must | docs = code | partial |
| AR-10.6 | Could | new formats as adapters | n/a |

---

## Definition of Done (для этого документа)

- [x] Секции AR-1…AR-10
- [x] Таблицы ID | P | критерий | модули | риск
- [x] Compliance as-is
- [x] Non-goals
- [x] Согласование с ADR 0001; Proposed ADR только маркерами
- [x] ≥15 Must-требований

---

## История

| Дата | Изменение |
|------|-----------|
| 2026-07-27 | Первичная фиксация Architecture Requirements по коду и ADR 0001 |
| 2026-07-27 | P0: ports unify, --strict/MediaError, JSON SoT, CI, tests, docs |
| 2026-07-27 | Sync compliance + GH issues with as-is (~89 tests, engine ~1108, shim gone) |
