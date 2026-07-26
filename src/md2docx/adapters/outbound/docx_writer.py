"""DocumentWriter adapter: DocumentModel → .docx."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, Twips

from md2docx.adapters.outbound import docx_engine as eng
from md2docx.domain.list_markers import (
    LIST_LEFT_TWIPS,
    LIST_MARKER_PREFIX,
    LIST_STYLE_DASH,
    LIST_STYLE_NUM,
)
from md2docx.domain.model import (
    CodeLine,
    DocumentModel,
    EmptyLine,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    Table,
)
from md2docx.domain.stylespec import RenderOptions


class DocxWriter:
    def write(
        self,
        model: DocumentModel,
        options: RenderOptions,
        dest: Path,
    ) -> Path:
        doc = Document()
        eng.apply_gost_styles(doc, **options.as_style_kwargs())
        self._write_title(doc, model)
        formula_n = 0
        for block in model.blocks:
            formula_n = self._write_block(doc, block, formula_n)
        if options.page_numbers:
            eng.setup_page_numbers(doc)
        dest = Path(dest)
        doc.save(str(dest))
        return dest

    def restyle(
        self,
        source: Path,
        dest: Path,
        options: RenderOptions,
    ) -> Path:
        return Path(
            eng.restyle_docx(
                source,
                dest,
                style_opts=options.as_style_kwargs(),
                page_numbers=options.page_numbers,
            )
        )

    def write_demo(self, options: RenderOptions, dest: Path) -> Path:
        return Path(
            eng.build_demo(
                str(dest),
                style_opts=options.as_style_kwargs(),
                page_numbers=options.page_numbers,
            )
        )

    def _write_title(self, doc: Document, model: DocumentModel) -> None:
        t = model.title
        if not (t.org or t.topic or t.city_year):
            return
        if t.org:
            doc.add_paragraph(t.org, style="TitleOrg")
        doc.add_paragraph(
            "ОТЧЁТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ", style="TitleDocType"
        )
        if t.topic:
            doc.add_paragraph(t.topic, style="TitleTopic")
        if t.city_year:
            doc.add_paragraph(t.city_year, style="TitleCityYear")

    def _write_block(self, doc: Document, block, formula_n: int) -> int:
        if isinstance(block, Heading):
            if block.structural:
                eng.add_paragraph_formatted(
                    doc, block.text, style="StructuralHeading"
                )
            elif block.level <= 1:
                eng.add_paragraph_formatted(doc, block.text, style="Heading 1")
            elif block.level == 2:
                eng.add_paragraph_formatted(doc, block.text, style="Heading 2")
            else:
                eng.add_paragraph_formatted(doc, block.text, style="Heading 3")
        elif isinstance(block, Paragraph):
            eng.add_paragraph_formatted(doc, block.text, style="Normal")
        elif isinstance(block, ListItem):
            if block.ordered:
                p = doc.add_paragraph(style=LIST_STYLE_NUM)
                n = block.index or 1
                p.add_run(f"{n}) ")
                eng.add_runs_with_scripts(p, block.text)
            else:
                p = doc.add_paragraph(style=LIST_STYLE_DASH)
                p.add_run(LIST_MARKER_PREFIX)
                eng.add_runs_with_scripts(p, block.text)
                try:
                    p.paragraph_format.tab_stops.clear_all()
                except Exception:
                    pass
                p.paragraph_format.tab_stops.add_tab_stop(
                    Twips(LIST_LEFT_TWIPS), alignment=WD_TAB_ALIGNMENT.LEFT
                )
            pPr = p._p.get_or_add_pPr()
            for child in list(pPr):
                if child.tag == qn("w:numPr"):
                    pPr.remove(child)
        elif isinstance(block, Table):
            if block.caption:
                eng.add_paragraph_formatted(
                    doc, block.caption, style="CaptionTable"
                )
            if block.rows:
                cols = max(len(r) for r in block.rows)
                table = doc.add_table(rows=len(block.rows), cols=cols)
                table.style = "Table Grid"
                for r_idx, row in enumerate(block.rows):
                    for c_idx in range(cols):
                        cell = table.cell(r_idx, c_idx)
                        text = row[c_idx] if c_idx < len(row) else ""
                        text = text.replace("<br>", "\n").replace("<br/>", "\n")
                        style_name = (
                            "TableHeader" if r_idx == 0 else "TableCell"
                        )
                        eng.fill_table_cell(
                            cell, text, style_name=style_name
                        )
                eng.add_empty_line(doc)
        elif isinstance(block, Figure):
            if block.path:
                from pathlib import Path as P

                img = P(block.path)
                if img.is_file():
                    try:
                        doc.add_picture(str(img), width=Mm(140))
                        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    except Exception:
                        pass
            cap = eng.add_paragraph_formatted(
                doc, block.caption, style="CaptionFigure"
            )
            if block.path:
                cap.paragraph_format.space_before = Pt(0)
        elif isinstance(block, Formula):
            formula_n += 1
            p = doc.add_paragraph(style="Formula")
            eng.add_runs_with_scripts(p, block.text)
            p.add_run(f"\t({formula_n})")
        elif isinstance(block, Quote):
            eng.add_paragraph_formatted(doc, block.text, style="Quote")
        elif isinstance(block, CodeLine):
            doc.add_paragraph(block.text if block.text else " ", style="CodeBlock")
        elif isinstance(block, EmptyLine):
            eng.add_empty_line(doc)
        return formula_n
