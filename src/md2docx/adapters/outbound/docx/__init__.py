"""DOCX outbound subpackage (styles, page, runs, cells, restyle)."""

from md2docx.adapters.outbound.docx.cells import (
    add_empty_line,
    apply_cell_paragraph_spacing,
    fill_table_cell,
)
from md2docx.adapters.outbound.docx.helpers import (
    _get_or_add_paragraph_style,
    _get_style_by_name,
    _set_run_font,
    _strip_num_pr,
)
from md2docx.adapters.outbound.docx.page import (
    add_figure_picture,
    apply_gost_page_setup,
    read_section_page_setup,
    section_text_height_mm,
    section_text_width_mm,
    set_section_page,
)
from md2docx.adapters.outbound.docx.page_numbers import (
    add_page_number_field,
    setup_page_numbers,
)
from md2docx.adapters.outbound.docx.restyle import (
    remove_unused_styles,
    restyle_docx,
)
from md2docx.adapters.outbound.docx.runs import (
    add_paragraph_formatted,
    add_runs_from_spans,
    add_runs_with_scripts,
)
from md2docx.adapters.outbound.docx.styles import apply_gost_styles

__all__ = [
    "add_empty_line",
    "add_figure_picture",
    "add_page_number_field",
    "add_paragraph_formatted",
    "add_runs_from_spans",
    "add_runs_with_scripts",
    "apply_cell_paragraph_spacing",
    "apply_gost_page_setup",
    "apply_gost_styles",
    "fill_table_cell",
    "read_section_page_setup",
    "remove_unused_styles",
    "restyle_docx",
    "section_text_height_mm",
    "section_text_width_mm",
    "set_section_page",
    "setup_page_numbers",
    "_get_style_by_name",
    "_get_or_add_paragraph_style",
    "_set_run_font",
    "_strip_num_pr",
]
