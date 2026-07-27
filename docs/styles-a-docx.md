# Карта стилей A.docx → md2docx

Стили создаются/накладываются в `adapters/outbound/docx/styles.py`
(`apply_gost_styles`). Lookup по **видимому имени** стиля (не по style_id).

| A.docx (источник) | Имя стиля в md2docx | Назначение |
|-------------------|---------------------|------------|
| Normal | Normal | основной текст, firstLine ~851 twips, 1.5, TNR 12 |
| @Header1 | StructuralHeading | 16 pt CAPS center, page break |
| @Header2 | Heading 1 | 14 pt CAPS, page break |
| @Header3 | Heading 2 | 14 pt, hanging / first line, empty before |
| @Header4 | Heading 3 | 12 pt bold+italic, empty before |
| @Title.Table | CaptionTable | left, empty line before |
| @Title.Picture | CaptionFigure | center, empty before/after |
| @Table.Text | TableCell | 10 pt, center, pad ~3 pt |
| @Table.Header-C | TableHeader | заголовок таблицы |
| @Foot-note | FootnoteText | 10 pt |
| toc 1–3 | toc 1 / toc 2 / toc 3 | оглавление |
| — | TitleOrg, TitleDocType, TitleTopic, TitleCityYear | титул |
| — | Formula, Quote, CodeBlock, Bibliography | спец. блоки |
| — | GostListDash, GostListNumber | списки **без** Word numPr |
| — | FooterPageNumber | номер страницы |

Списки: **не** List Bullet / List Number Word; маркер «—» + tab для dash.

## Поля страницы (defaults)

| Поле | mm |
|------|-----|
| left | 30 |
| right | 15 |
| top | 20 |
| bottom | 20 |
| width × height | 210 × 297 (A4 portrait logical) |

При multi-section: у каждой секции свой `PageSetup` (orientation, size, margins).
`--restyle` **сохраняет** ориентацию/размер/поля секций.

## Машиночитаемый профиль

`src/md2docx/config/gost-7.32-2017-styles.json`

```bash
python -m md2docx -i sample.md -o out.docx --config src/md2docx/config/gost-7.32-2017-styles.json
```

## См. также

- [markdown-features.md](markdown-features.md)
- [user-guide.md](user-guide.md)
