"""DOCX low-level helpers (split from former docx_engine)."""

from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Mm, RGBColor, Twips

from md2docx.adapters.outbound.docx_list_layout import (
    LIST_HANGING_TWIPS,
    LIST_LEFT_TWIPS,
)
from md2docx.domain.list_markers import (
    LIST_STYLE_DASH,
    LIST_STYLE_NUM,
)
from md2docx.domain.stylespec import (
    A_FOOTNOTE_PT,
    A_H2_FIRST_LINE_TWIPS,
    A_H3_HANGING_TWIPS,
    A_H3_LEFT_TWIPS,
    A_HEADER1_PT,
    A_HEADER2_PT,
    A_HEADER3_PT,
    A_HEADER4_PT,
    A_LINE_100,
    A_LINE_125,
    A_LINE_150,
    A_NORMAL_FIRST_LINE_TWIPS,
    A_REF_BEFORE_PT,
    A_TABLE_CELL_PAD_PT,
    A_TABLE_HEADER_LEFT_TWIPS,
    A_TOC1_AFTER_PT,
    A_TOC2_AFTER_PT,
    A_TOC2_BEFORE_PT,
    A_TOC2_HANGING_TWIPS,
    A_TOC2_LEFT_TWIPS,
    A_TOC3_AFTER_PT,
    A_TOC3_BEFORE_PT,
    A_TOC3_HANGING_TWIPS,
    A_TOC3_LEFT_TWIPS,
    A_TOC3_PT,
    BODY_PT,
    EMPTY_LINE_PT,
    FIRST_LINE_MM,
    FONT,
    LINE_1_5,
    PAGE_DEFAULT,
    SMALL_PT,
    TABLE_PT,
)

PAGE = PAGE_DEFAULT
HEADING_COLOR = RGBColor(0x00, 0x00, 0x00)

ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "both": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

from md2docx.adapters.outbound.docx.cells import _set_paragraph
from md2docx.adapters.outbound.docx.helpers import (
    _get_or_add_paragraph_style,
    _get_style_by_name,
    _set_run_font,
    _strip_num_pr,
)
from md2docx.adapters.outbound.docx.page import apply_gost_page_setup


def apply_gost_styles(
    doc: Document,
    *,
    font: str = FONT,
    body_pt: float = BODY_PT,
    table_pt: float = TABLE_PT,
    small_pt: float = SMALL_PT,
    line_spacing: float = LINE_1_5,
    first_line_mm: float = FIRST_LINE_MM,
    page: dict[str, float] | None = None,
) -> Document:
    """Стили по A.docx (заголовки, абзацы, подписи, таблицы, TOC, сноски) + поля ГОСТ."""
    apply_gost_page_setup(doc, page)
    p = page or PAGE
    content_width_mm = p["width_mm"] - p["left_mm"] - p["right_mm"]

    # --- Normal ← A.docx Normal (firstLine 851, both, 1.5, TNR 12) ---
    normal = _get_style_by_name(doc, "Normal")
    _set_run_font(normal, font=font, size_pt=body_pt)
    if abs(first_line_mm - FIRST_LINE_MM) < 0.05:
        _set_paragraph(
            normal,
            alignment="both",
            first_line_twips=A_NORMAL_FIRST_LINE_TWIPS,
            left_twips=0,
            line_spacing=line_spacing,
        )
    else:
        _set_paragraph(
            normal,
            alignment="both",
            first_line_mm=first_line_mm,
            line_spacing=line_spacing,
        )

    # --- Заголовки @Header1…@Header4 (все чёрные) ---
    # @Header1 → StructuralHeading: с новой страницы
    st = _get_or_add_paragraph_style(doc, "StructuralHeading")
    st.base_style = normal
    st.quick_style = True
    _set_run_font(
        st, font=font, size_pt=A_HEADER1_PT, bold=False, all_caps=True, color=HEADING_COLOR
    )
    _set_paragraph(
        st,
        alignment="center",
        first_line_mm=0,
        before_pt=0,
        after_pt=0,
        line_spacing=A_LINE_125,
        keep_with_next=True,
        page_break_before=True,
        outline_level=0,
    )

    # @Header2 → Heading 1: разрыв страницы перед заголовком
    h1 = _get_style_by_name(doc, "Heading 1")
    h1.base_style = normal
    _set_run_font(
        h1, font=font, size_pt=A_HEADER2_PT, bold=False, all_caps=True, color=HEADING_COLOR
    )
    _set_paragraph(
        h1,
        alignment="left",
        first_line_twips=A_H2_FIRST_LINE_TWIPS,
        left_twips=0,
        before_pt=0,
        after_pt=0,
        line_spacing=A_LINE_150,
        keep_with_next=True,
        page_break_before=True,
        outline_level=0,
    )

    # @Header3 → Heading 2: пустая строка перед
    h2 = _get_style_by_name(doc, "Heading 2")
    h2.base_style = normal
    _set_run_font(
        h2, font=font, size_pt=A_HEADER3_PT, bold=False, all_caps=False, color=HEADING_COLOR
    )
    _set_paragraph(
        h2,
        alignment="left",
        left_twips=A_H3_LEFT_TWIPS,
        hanging_twips=A_H3_HANGING_TWIPS,
        before_pt=EMPTY_LINE_PT,
        after_pt=0,
        line_spacing=A_LINE_125,
        keep_with_next=True,
        page_break_before=False,
        outline_level=1,
    )

    # @Header4 → Heading 3: пустая строка перед
    h3 = _get_style_by_name(doc, "Heading 3")
    h3.base_style = normal
    _set_run_font(
        h3,
        font=font,
        size_pt=A_HEADER4_PT,
        bold=True,
        italic=True,
        all_caps=False,
        color=HEADING_COLOR,
    )
    _set_paragraph(
        h3,
        alignment="left",
        left_twips=A_H3_LEFT_TWIPS,
        hanging_twips=A_H3_HANGING_TWIPS,
        before_pt=EMPTY_LINE_PT,
        after_pt=0,
        line_spacing=A_LINE_125,
        keep_with_next=True,
        page_break_before=False,
        outline_level=2,
    )

    # --- Подписи: @Title.Table / @Title.Picture ---
    # пустая строка ПЕРЕД названием таблицы; ПОСЛЕ таблицы — add_empty_line() в контенте;
    # пустая строка ПЕРЕД рисунком (caption/image) + ПОСЛЕ подписи рисунка
    cap_t = _get_or_add_paragraph_style(doc, "CaptionTable")
    cap_t.base_style = normal
    _set_run_font(cap_t, font=font, size_pt=body_pt, color=HEADING_COLOR)
    _set_paragraph(
        cap_t,
        alignment="left",
        first_line_mm=0,
        before_pt=EMPTY_LINE_PT,
        after_pt=0,
        line_spacing=A_LINE_125,
        keep_with_next=True,
    )

    cap_f = _get_or_add_paragraph_style(doc, "CaptionFigure")
    cap_f.base_style = normal
    _set_run_font(cap_f, font=font, size_pt=body_pt, color=HEADING_COLOR)
    _set_paragraph(
        cap_f,
        alignment="center",
        first_line_mm=0,
        before_pt=EMPTY_LINE_PT,
        after_pt=EMPTY_LINE_PT,
        line_spacing=A_LINE_125,
        keep_with_next=False,
    )

    # --- Таблицы: @Table.Text / @Table.Header-C / @Table.Header-L ---
    # default 3pt/3pt для одного абзаца; multi-para — fill_table_cell / apply_cell_paragraph_spacing
    tc = _get_or_add_paragraph_style(doc, "TableCell")
    tc.base_style = normal
    _set_run_font(tc, font=font, size_pt=table_pt, color=HEADING_COLOR)
    _set_paragraph(
        tc,
        alignment="center",
        first_line_mm=0,
        before_pt=A_TABLE_CELL_PAD_PT,
        after_pt=A_TABLE_CELL_PAD_PT,
        line_spacing=A_LINE_100,
    )

    th = _get_or_add_paragraph_style(doc, "TableHeader")
    th.base_style = normal
    _set_run_font(th, font=font, size_pt=table_pt, bold=False, color=HEADING_COLOR)
    _set_paragraph(
        th,
        alignment="center",
        first_line_mm=0,
        before_pt=A_TABLE_CELL_PAD_PT,
        after_pt=A_TABLE_CELL_PAD_PT,
        line_spacing=A_LINE_100,
        keep_with_next=True,
    )

    thl = _get_or_add_paragraph_style(doc, "TableHeaderLeft")
    thl.base_style = normal
    _set_run_font(thl, font=font, size_pt=table_pt, bold=False, color=HEADING_COLOR)
    _set_paragraph(
        thl,
        alignment="left",
        first_line_twips=0,
        left_twips=A_TABLE_HEADER_LEFT_TWIPS,
        before_pt=A_TABLE_CELL_PAD_PT,
        after_pt=A_TABLE_CELL_PAD_PT,
        line_spacing=A_LINE_100,
        keep_with_next=True,
    )

    # --- Формула (в A.docx отдельного стиля нет — center + правый таб номера) ---
    formula = _get_or_add_paragraph_style(doc, "Formula")
    formula.base_style = normal
    _set_run_font(formula, font=font, size_pt=body_pt)
    _set_paragraph(
        formula,
        alignment="center",
        first_line_mm=0,
        before_pt=6,
        after_pt=6,
        line_spacing=line_spacing,
    )
    try:
        formula.paragraph_format.tab_stops.clear_all()
    except Exception:
        pass
    formula.paragraph_format.tab_stops.add_tab_stop(
        Mm(content_width_mm), alignment=WD_TAB_ALIGNMENT.RIGHT
    )

    # --- Списки (маркер/номер в тексте, БЕЗ w:numPr — иначе Word рисует •) ---
    # GostListDash: ненумерованный, префикс «—\t»
    ls_dash = _get_or_add_paragraph_style(doc, LIST_STYLE_DASH)
    ls_dash.base_style = normal
    # имя = LIST_STYLE_DASH (не переименовывать — иначе lookup по style_id → UserWarning)
    _set_run_font(ls_dash, font=font, size_pt=body_pt, color=HEADING_COLOR)
    _set_paragraph(
        ls_dash,
        alignment="both",
        left_twips=LIST_LEFT_TWIPS,
        hanging_twips=LIST_HANGING_TWIPS,
        line_spacing=line_spacing,
    )
    _strip_num_pr(ls_dash)
    # табуляция после «—» → текст с позиции left indent
    try:
        ls_dash.paragraph_format.tab_stops.clear_all()
    except Exception:
        pass
    ls_dash.paragraph_format.tab_stops.add_tab_stop(
        Twips(LIST_LEFT_TWIPS), alignment=WD_TAB_ALIGNMENT.LEFT
    )

    # GostListNumber: нумерованный, префикс «1) » в тексте
    ls_num = _get_or_add_paragraph_style(doc, LIST_STYLE_NUM)
    ls_num.base_style = normal
    _set_run_font(ls_num, font=font, size_pt=body_pt, color=HEADING_COLOR)
    _set_paragraph(
        ls_num,
        alignment="both",
        left_twips=LIST_LEFT_TWIPS,
        hanging_twips=LIST_HANGING_TWIPS,
        line_spacing=line_spacing,
    )
    _strip_num_pr(ls_num)

    # На всякий случай снять буллеты со встроенных List Bullet / List Number
    for builtin in ("List Bullet", "List Number", "List Paragraph"):
        try:
            _strip_num_pr(_get_style_by_name(doc, builtin))
        except KeyError:
            pass

    # --- Библиография ← @Paragraph s1.0_i0.0 (ссылки [1] …) ---
    bib = _get_or_add_paragraph_style(doc, "Bibliography")
    bib.base_style = normal
    _set_run_font(bib, font=font, size_pt=body_pt)
    _set_paragraph(
        bib,
        alignment="both",
        first_line_mm=0,
        before_pt=A_REF_BEFORE_PT,
        after_pt=A_REF_BEFORE_PT,
        line_spacing=A_LINE_100,
    )

    # --- Цитата ← Quote (курсив, как Normal) ---
    quote = _get_or_add_paragraph_style(doc, "Quote")
    quote.base_style = normal
    _set_run_font(quote, font=font, size_pt=body_pt, italic=True)
    if abs(first_line_mm - FIRST_LINE_MM) < 0.05:
        _set_paragraph(
            quote,
            alignment="both",
            first_line_twips=A_NORMAL_FIRST_LINE_TWIPS,
            line_spacing=line_spacing,
        )
    else:
        _set_paragraph(
            quote,
            alignment="both",
            first_line_mm=first_line_mm,
            line_spacing=line_spacing,
        )

    # --- Сноска ← @Foot-note (10 pt, без абзацного отступа) ---
    fn = _get_or_add_paragraph_style(doc, "FootnoteText")
    fn.base_style = normal
    _set_run_font(fn, font=font, size_pt=A_FOOTNOTE_PT)
    _set_paragraph(
        fn,
        alignment="left",
        first_line_mm=0,
        before_pt=0,
        after_pt=0,
        line_spacing=A_LINE_100,
    )
    # встроенный стиль Word «footnote text», если есть
    try:
        fnt = _get_style_by_name(doc, "footnote text")
        _set_run_font(fnt, font=font, size_pt=A_FOOTNOTE_PT)
        _set_paragraph(
            fnt,
            alignment="left",
            first_line_mm=0,
            line_spacing=A_LINE_100,
        )
    except KeyError:
        pass

    # --- Оглавление toc 1…3 (как в A.docx) ---
    toc1 = _get_or_add_paragraph_style(doc, "toc 1")
    toc1.base_style = normal
    _set_run_font(toc1, font=font, size_pt=body_pt)
    _set_paragraph(
        toc1,
        alignment="left",
        first_line_mm=0,
        before_pt=0,
        after_pt=A_TOC1_AFTER_PT,
        line_spacing=line_spacing,
    )

    toc2 = _get_or_add_paragraph_style(doc, "toc 2")
    toc2.base_style = normal
    _set_run_font(toc2, font=font, size_pt=body_pt, all_caps=True)
    _set_paragraph(
        toc2,
        alignment="left",
        left_twips=A_TOC2_LEFT_TWIPS,
        hanging_twips=A_TOC2_HANGING_TWIPS,
        before_pt=A_TOC2_BEFORE_PT,
        after_pt=A_TOC2_AFTER_PT,
        line_spacing=line_spacing,
    )

    toc3 = _get_or_add_paragraph_style(doc, "toc 3")
    toc3.base_style = normal
    _set_run_font(toc3, font=font, size_pt=A_TOC3_PT)
    _set_paragraph(
        toc3,
        alignment="left",
        left_twips=A_TOC3_LEFT_TWIPS,
        hanging_twips=A_TOC3_HANGING_TWIPS,
        before_pt=A_TOC3_BEFORE_PT,
        after_pt=A_TOC3_AFTER_PT,
        line_spacing=A_LINE_125,
    )

    # --- Колонтитул / номер страницы ---
    foot = _get_or_add_paragraph_style(doc, "FooterPageNumber")
    foot.base_style = normal
    _set_run_font(foot, font=font, size_pt=body_pt)
    _set_paragraph(
        foot,
        alignment="center",
        first_line_mm=0,
        line_spacing=A_LINE_100,
    )
    try:
        footer_style = _get_style_by_name(doc, "Footer")
        _set_run_font(footer_style, font=font, size_pt=body_pt)
        _set_paragraph(
            footer_style,
            alignment="center",
            first_line_mm=0,
            line_spacing=A_LINE_100,
        )
    except KeyError:
        pass

    # --- Титул (A.docx @Frontpage.*) + служебные ---
    title_specs = [
        ("TitleOrg", body_pt, True, False, "center", 0, 0, line_spacing),
        ("TitleDocType", body_pt, True, True, "center", 24, 12, line_spacing),
        ("TitleTopic", body_pt, False, True, "center", 12, 12, line_spacing),
        ("TitleMeta", body_pt, False, False, "left", 0, 0, line_spacing),
        ("TitleCityYear", body_pt, False, False, "center", 0, 0, line_spacing),
        ("CodeBlock", small_pt, False, False, "left", 6, 6, A_LINE_100),
    ]
    for style_id, size, caps, bold, align, before, after, ls in title_specs:
        est = _get_or_add_paragraph_style(doc, style_id)
        est.base_style = normal
        use_font = "Courier New" if style_id == "CodeBlock" else font
        _set_run_font(est, font=use_font, size_pt=size, bold=bold, all_caps=caps)
        _set_paragraph(
            est,
            alignment=align,
            first_line_mm=0,
            before_pt=before,
            after_pt=after,
            line_spacing=ls,
        )

    return doc
