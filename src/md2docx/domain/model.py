"""Доменная модель документа (независимо от Word)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from md2docx.domain.page import PageSetup, page_setup_default
from md2docx.domain.spans import TextSpan


@dataclass
class TitleMeta:
    org: str | None = None
    topic: str | None = None
    city_year: str | None = None


@dataclass
class Heading:
    level: int  # 1..3
    text: str
    structural: bool = False


@dataclass
class Paragraph:
    text: str
    spans: list[TextSpan] | None = None


@dataclass
class ListItem:
    text: str
    ordered: bool = False
    index: int | None = None  # 1-based for ordered
    spans: list[TextSpan] | None = None


@dataclass
class Table:
    rows: list[list[str]]
    caption: str | None = None


@dataclass
class Figure:
    caption: str
    path: str | None = None


@dataclass
class Formula:
    text: str


@dataclass
class Quote:
    text: str


@dataclass
class CodeLine:
    text: str


@dataclass
class EmptyLine:
    pass


@dataclass
class SectionBreak:
    """Начало секции с указанным PageSetup (контент после маркера — в этой секции)."""

    setup: PageSetup = field(default_factory=page_setup_default)


Block = Union[
    Heading,
    Paragraph,
    ListItem,
    Table,
    Figure,
    Formula,
    Quote,
    CodeLine,
    EmptyLine,
    SectionBreak,
]


@dataclass
class DocumentModel:
    title: TitleMeta = field(default_factory=TitleMeta)
    default_page: PageSetup = field(default_factory=page_setup_default)
    blocks: list[Block] = field(default_factory=list)
