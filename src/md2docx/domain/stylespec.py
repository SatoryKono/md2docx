"""Параметры оформления (значения по умолчанию; JSON может перекрыть)."""

from __future__ import annotations

from dataclasses import dataclass, field


FONT = "Times New Roman"
BODY_PT = 12.0
TABLE_PT = 10.0
SMALL_PT = 12.0
LINE_1_5 = 1.5
FIRST_LINE_MM = 15.0

A_LINE_100 = 1.0
A_LINE_125 = 300 / 240
A_LINE_150 = 360 / 240
A_NORMAL_FIRST_LINE_TWIPS = 851
A_HEADER1_PT = 16
A_HEADER2_PT = 14
A_HEADER3_PT = 14
A_HEADER4_PT = 12
A_H2_FIRST_LINE_TWIPS = 720
A_H3_LEFT_TWIPS = 1560
A_H3_HANGING_TWIPS = 709
A_FOOTNOTE_PT = 10
A_TABLE_CELL_PAD_PT = 3
A_TABLE_HEADER_LEFT_TWIPS = 113
A_REF_BEFORE_PT = 2
A_TOC1_AFTER_PT = 5
A_TOC2_BEFORE_PT = 10
A_TOC2_AFTER_PT = 4
A_TOC2_LEFT_TWIPS = 1418
A_TOC2_HANGING_TWIPS = 851
A_TOC3_BEFORE_PT = 3
A_TOC3_AFTER_PT = 1
A_TOC3_LEFT_TWIPS = 2410
A_TOC3_HANGING_TWIPS = 974
A_TOC3_PT = 12
EMPTY_LINE_PT = BODY_PT * LINE_1_5

PAGE_DEFAULT: dict[str, float] = {
    "width_mm": 210,
    "height_mm": 297,
    "left_mm": 30,
    "right_mm": 15,
    "top_mm": 20,
    "bottom_mm": 20,
}

STYLE_NAMES = [
    "Normal",
    "StructuralHeading",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "CaptionTable",
    "CaptionFigure",
    "TableCell",
    "TableHeader",
    "TableHeaderLeft",
    "Formula",
    "GostListDash",
    "GostListNumber",
    "Bibliography",
    "Quote",
    "FooterPageNumber",
    "TitleOrg",
    "TitleDocType",
    "TitleTopic",
    "TitleMeta",
    "TitleCityYear",
    "CodeBlock",
    "FootnoteText",
    "toc 1",
    "toc 2",
    "toc 3",
]


@dataclass
class RenderOptions:
    font: str = FONT
    body_pt: float = BODY_PT
    table_pt: float = TABLE_PT
    small_pt: float = SMALL_PT
    line_spacing: float = LINE_1_5
    first_line_mm: float = FIRST_LINE_MM
    page: dict[str, float] = field(default_factory=lambda: dict(PAGE_DEFAULT))
    page_numbers: bool = True

    def as_style_kwargs(self) -> dict:
        return {
            "font": self.font,
            "body_pt": self.body_pt,
            "table_pt": self.table_pt,
            "small_pt": self.small_pt,
            "line_spacing": self.line_spacing,
            "first_line_mm": self.first_line_mm,
            "page": self.page,
        }


def default_render_options() -> RenderOptions:
    return RenderOptions()
