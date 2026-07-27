"""Compatibility facade — re-exports split DOCX modules.

Prefer: `from md2docx.adapters.outbound import docx` or submodule imports.
Demo content lives in domain.demo_document + DocumentWriter.write.
"""

from md2docx.adapters.outbound.docx import *  # noqa: F403
from md2docx.adapters.outbound.docx import (  # noqa: F401
    _get_or_add_paragraph_style,
    _get_style_by_name,
    _set_run_font,
    _strip_num_pr,
    add_empty_line,
    add_figure_picture,
    add_page_number_field,
    add_paragraph_formatted,
    add_runs_from_spans,
    add_runs_with_scripts,
    apply_cell_paragraph_spacing,
    apply_gost_page_setup,
    apply_gost_styles,
    fill_table_cell,
    read_section_page_setup,
    remove_unused_styles,
    restyle_docx,
    section_text_height_mm,
    section_text_width_mm,
    set_section_page,
    setup_page_numbers,
)
