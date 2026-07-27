# ADR 0002: Presentation constants (twips / Word style names)

## Статус

Accepted (2026-07-27)

## Контекст

AR-3.6: domain не должен экспортировать Word twips / OOXML style names как API.

## Решение

- Domain `list_markers`: семантика маркера (`LIST_MARKER_PREFIX`) + **legacy** style name aliases for Word list styles (string constants used as role keys).
- Word layout numbers (`LIST_*_TWIPS`) → `adapters.outbound.docx_list_layout`.
- `stylespec` keeps A.docx measurement constants used by styles adapter (presentation VO shared with outbound); full purification of stylespec is follow-up if needed.

## Последствия

Adapters own twips. Domain remains free of python-docx.
