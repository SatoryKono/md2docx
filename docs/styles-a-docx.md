# Карта стилей A.docx → md2docx

| A.docx | Word style id | Назначение |
|--------|---------------|------------|
| Normal | Normal | основной текст, firstLine 851, 1.5 |
| @Header1 | StructuralHeading | 16 pt CAPS center, page break |
| @Header2 | Heading 1 | 14 pt CAPS, page break, firstLine 720 |
| @Header3 | Heading 2 | 14 pt, hanging, empty line before |
| @Header4 | Heading 3 | 12 pt bold+italic, empty line before |
| @Title.Table | CaptionTable | left, empty line before |
| @Title.Picture | CaptionFigure | center, empty before/after |
| @Table.Text | TableCell | 10 pt, center, 3 pt pad |
| @Table.Header-C | TableHeader | center header |
| @Foot-note | FootnoteText | 10 pt |
| toc 1–3 | toc 1–3 | оглавление |

Списки: **не** List Bullet; `GostListDash` / `GostListNumber`.

Машиночитаемый профиль: `src/md2docx/config/gost-7.32-2017-styles.json`.
