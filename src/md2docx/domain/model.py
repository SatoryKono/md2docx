"""Доменная модель документа (независимо от Word)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


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


@dataclass
class ListItem:
    text: str
    ordered: bool = False
    index: int | None = None  # 1-based for ordered


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
]


@dataclass
class DocumentModel:
    title: TitleMeta = field(default_factory=TitleMeta)
    blocks: list[Block] = field(default_factory=list)
