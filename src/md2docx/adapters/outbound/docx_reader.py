"""DOCX → DocumentModel (outbound adapter).

Поддержка md2docx-стилей и эталона A.docx (@Header*, @Common, toc, media).
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from md2docx.domain.list_markers import LIST_STYLE_DASH, LIST_STYLE_NUM
from md2docx.domain.model import (
    CodeLine,
    DocumentModel,
    Figure,
    Formula,
    Heading,
    ListItem,
    Paragraph,
    Quote,
    SectionBreak,
    Table,
    TitleMeta,
)
from md2docx.domain.page import PageSetup, page_setup_default
from md2docx.domain.scripts import segments_to_markdown
from md2docx.domain.structural import is_structural_heading

_R_EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
_A_BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

_A_STYLE_ALIASES = {
    "@Header1": "StructuralHeading",
    "@Header2": "Heading 1",
    "@Header3": "Heading 2",
    "@Header4": "Heading 3",
    "@Header5": "Heading 3",
    "@Header6": "Heading 3",
    "Heading 4": "Heading 3",
    "Heading 5": "Heading 3",
    "@Common": "Normal",
    "@Paragraph": "Normal",
    "@Paragraph s1.0_i0.0": "Bibliography",
    "@Title.Table": "CaptionTable",
    "@Title.Picture": "CaptionFigure",
    "@Foot-note": "FootnoteText",
    "First Paragraph": "Normal",
}

_FORMULA_NUM_RE = re.compile(r"[\t ]*\(\d+\)\s*$")
_ORDERED_PREFIX = re.compile(r"^(\d+)\)\s*")
_DASH_PREFIX = re.compile(r"^[\u2014\u2013\-]\s*")
_TOC_LINE_RE = re.compile(r"^[\d§.]+\s+\S.+\s+\d{1,3}\s*$", re.UNICODE)
_TABLE_CAPTION_RE = re.compile(
    r"^Таблица(\s+\d+([.,]\d+)*)?\b.*$",
    re.IGNORECASE | re.UNICODE,
)
_FIGURE_CAPTION_RE = re.compile(
    r"^Рисунок(\s+\d+([.,]\d+)*)?\b.*$",
    re.IGNORECASE | re.UNICODE,
)
_BIB_RE = re.compile(r"^\[(\d+)\]\s*(.*)$", re.UNICODE)
_LIST_DASH_RE = re.compile(r"^[\u2014\u2013•·]\s+(.+)$", re.UNICODE)
_LIST_HYPHEN_RE = re.compile(r"^[-*]\s+(.+)$")
_SECTION_START_RE = re.compile(r"^(\d+|§\s*\d+)\b")


def _iter_body_blocks(doc: Document):
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield DocxParagraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield DocxTable(child, doc)


def _paragraph_md_text(p: DocxParagraph) -> str:
    segs: list[tuple[str, str]] = []
    for run in p.runs:
        t = run.text
        if t is None or t == "":
            continue
        if run.font.subscript:
            segs.append(("sub", t))
        elif run.font.superscript:
            segs.append(("super", t))
        else:
            segs.append(("plain", t))
    return segments_to_markdown(segs)


def _style_name(p: DocxParagraph) -> str:
    try:
        name = p.style.name if p.style is not None else "Normal"
    except Exception:
        name = "Normal"
    if name.lower().startswith("toc"):
        return "TOC"
    return _A_STYLE_ALIASES.get(name, name)


def _is_toc_line(text: str) -> bool:
    t = text.strip()
    if not t or len(t) > 220:
        return False
    if _TOC_LINE_RE.match(t):
        return True
    if re.search(r"\.{2,}\s*\d{1,3}\s*$", t):
        return True
    return False


def _strip_list_prefix(text: str, ordered: bool) -> tuple[str, int | None]:
    if ordered:
        m = _ORDERED_PREFIX.match(text)
        if m:
            return text[m.end() :], int(m.group(1))
        m2 = re.match(r"^(\d+)[.\)]\s+", text)
        if m2:
            return text[m2.end() :], int(m2.group(1))
        return text, None
    text2 = text.lstrip()
    if text2[:1] in ("\u2014", "\u2013", "-", "•", "·"):
        return text2[1:].lstrip("\t "), None
    m = _DASH_PREFIX.match(text)
    if m:
        return text[m.end() :], None
    return text, None


def _looks_like_section_heading(text: str) -> bool:
    return bool(_SECTION_START_RE.match(text.strip()))


class DocxReader:
    """Читает DOCX (md2docx и A.docx-подобные)."""

    def __init__(
        self,
        *,
        outline: bool = True,
        media_dir: Path | str | None = None,
    ) -> None:
        self.outline = outline
        self.media_dir = Path(media_dir) if media_dir else None

    def read(self, path: Path | str) -> DocumentModel:
        path = Path(path)
        doc = Document(str(path))
        title = TitleMeta()
        blocks: list = []
        pending_table_caption: str | None = None
        pending_image: Path | None = None
        code_run: list[str] = []
        media_dir = Path(self.media_dir) if self.media_dir else path.with_name(path.stem + "_media")
        image_n = 0
        body_started = not self.outline
        default_page = page_setup_default()
        section_slices = self._section_slices(doc)
        if section_slices:
            default_page = section_slices[0][0]

        def flush_code() -> None:
            nonlocal code_run
            for line in code_run:
                blocks.append(CodeLine(text=line if line != "" else " "))
            code_run = []

        def flush_pending_image(caption: str | None = None) -> None:
            """Закрепить рисунок без подписи, чтобы не потерять media при смене блока."""
            nonlocal pending_image
            if pending_image is None:
                return
            blocks.append(
                Figure(
                    caption=caption or "Рисунок",
                    path=str(pending_image),
                )
            )
            pending_image = None

        def take_image(p: DocxParagraph) -> Path | None:
            nonlocal image_n, pending_image
            got = self._extract_images(p, doc, media_dir, image_n)
            if got:
                # два drawing подряд — предыдущий без подписи, не перезаписывать
                if pending_image is not None:
                    flush_pending_image()
                image_n += 1
                pending_image = got
                return got
            return None

        prev_setup: PageSetup | None = None
        for sec_i, (setup, items) in enumerate(section_slices):
            setup = setup.normalized()
            if sec_i == 0:
                default_page = setup
                prev_setup = setup
            else:
                # только при реальной смене orient/size/margins
                if prev_setup is None or setup.differs_from(prev_setup):
                    blocks.append(SectionBreak(setup=setup))
                    prev_setup = setup
                # контент новых секций (в т.ч. landscape) всегда в body
                body_started = True

            for item in items:
                if isinstance(item, DocxTable):
                    if not body_started:
                        continue
                    flush_code()
                    flush_pending_image()
                    rows = self._read_table(item)
                    cap = pending_table_caption
                    pending_table_caption = None
                    if rows:
                        blocks.append(Table(rows=rows, caption=cap))
                    continue

                p: DocxParagraph = item
                style = _style_name(p)
                raw = p.text or ""

                if style == "TitleOrg":
                    flush_code()
                    title.org = raw.strip() or title.org
                    continue
                if style == "TitleDocType":
                    flush_code()
                    continue
                if style == "TitleTopic":
                    flush_code()
                    title.topic = raw.strip() or title.topic
                    continue
                if style in ("TitleCityYear", "TitleMeta"):
                    flush_code()
                    if style == "TitleCityYear":
                        title.city_year = raw.strip() or title.city_year
                    continue
                if style in ("Footer", "FooterPageNumber", "header", "Header", "TOC"):
                    continue

                if style == "CodeBlock":
                    if body_started:
                        code_run.append(raw if raw != " " else "")
                    continue
                flush_code()

                has_drawing = bool(p._element.findall(".//" + _A_BLIP))
                if not raw.strip() and not has_drawing:
                    continue

                md_text = _paragraph_md_text(p).replace("\t", " ").strip()
                raw_norm = raw.replace("\t", " ").strip()
                text = md_text or raw_norm

                if text and _is_toc_line(text):
                    continue

                if not body_started:
                    if style in (
                        "StructuralHeading",
                        "Heading 1",
                        "Heading 2",
                        "Heading 3",
                    ):
                        if is_structural_heading(text) or _looks_like_section_heading(text):
                            body_started = True
                        elif text and style in ("StructuralHeading", "Heading 1"):
                            if not any(isinstance(b, Heading) for b in blocks):
                                blocks.append(Heading(level=1, text=text, structural=True))
                            continue
                        else:
                            continue
                    else:
                        continue

                if not text and not has_drawing:
                    continue

                # drawing-only: копить media до подписи CaptionFigure
                if has_drawing and not text:
                    take_image(p)
                    continue

                is_fig_caption = style == "CaptionFigure" or (
                    bool(text)
                    and bool(_FIGURE_CAPTION_RE.match(text))
                    and style in ("Normal", "CaptionFigure")
                )
                # любой другой блок — pending-рисунок без подписи фиксируем
                if not is_fig_caption and not has_drawing:
                    flush_pending_image()

                if style == "StructuralHeading" and text:
                    blocks.append(Heading(level=1, text=text, structural=True))
                    continue
                if style == "Heading 1" and text:
                    blocks.append(
                        Heading(
                            level=1,
                            text=text,
                            structural=is_structural_heading(text),
                        )
                    )
                    continue
                if style == "Heading 2" and text:
                    blocks.append(Heading(level=2, text=text, structural=False))
                    continue
                if style == "Heading 3" and text:
                    blocks.append(Heading(level=3, text=text, structural=False))
                    continue

                if style == "CaptionTable" or (
                    text and _TABLE_CAPTION_RE.match(text) and style == "Normal"
                ):
                    pending_table_caption = text
                    continue

                if is_fig_caption:
                    take_image(p)
                    path_img = pending_image
                    pending_image = None
                    # caption-only (нет media) всё равно сохраняем для round-trip
                    blocks.append(
                        Figure(
                            caption=text or "Рисунок",
                            path=str(path_img) if path_img else None,
                        )
                    )
                    continue

                if style in (LIST_STYLE_DASH, "ГОСТ список (тире)", "GostListDash"):
                    body, _ = _strip_list_prefix(text, ordered=False)
                    blocks.append(ListItem(text=body.lstrip("\t "), ordered=False))
                    continue
                if style in (
                    LIST_STYLE_NUM,
                    "ГОСТ список (нумерация)",
                    "GostListNumber",
                ):
                    body, idx = _strip_list_prefix(text, ordered=True)
                    blocks.append(ListItem(text=body, ordered=True, index=idx))
                    continue

                if style == "Formula":
                    blocks.append(Formula(text=_FORMULA_NUM_RE.sub("", text).rstrip()))
                    continue

                if style == "Quote":
                    blocks.append(Quote(text=text))
                    continue

                if style == "Bibliography" or (text and _BIB_RE.match(text)):
                    m = _BIB_RE.match(text)
                    if m:
                        blocks.append(
                            ListItem(
                                text=(m.group(2).strip() or text),
                                ordered=True,
                                index=int(m.group(1)),
                            )
                        )
                    elif text:
                        blocks.append(Paragraph(text=text))
                    continue

                if has_drawing:
                    take_image(p)
                    path_img = pending_image
                    pending_image = None
                    blocks.append(
                        Figure(
                            caption=text or "Рисунок",
                            path=str(path_img) if path_img else None,
                        )
                    )
                    continue

                if text:
                    m = _LIST_DASH_RE.match(text) or _LIST_HYPHEN_RE.match(text)
                    if m:
                        blocks.append(ListItem(text=m.group(1).strip(), ordered=False))
                    else:
                        blocks.append(Paragraph(text=text))

        flush_code()
        flush_pending_image()
        return DocumentModel(title=title, blocks=blocks, default_page=default_page)

    def _section_slices(self, doc: Document) -> list[tuple[PageSetup, list]]:
        """Разбить body на (PageSetup, [paragraph|table]) по секциям Word."""
        from md2docx.adapters.outbound.docx_engine import read_section_page_setup

        setups: list[PageSetup] = [read_section_page_setup(s) for s in doc.sections]
        if not setups:
            setups = [page_setup_default()]

        buckets: list[list] = [[] for _ in setups]
        si = 0
        for child in doc.element.body.iterchildren():
            if child.tag == qn("w:sectPr"):
                continue
            if child.tag == qn("w:p"):
                buckets[min(si, len(buckets) - 1)].append(DocxParagraph(child, doc))
                pPr = child.find(qn("w:pPr"))
                if pPr is not None and pPr.find(qn("w:sectPr")) is not None:
                    if si < len(buckets) - 1:
                        si += 1
            elif child.tag == qn("w:tbl"):
                buckets[min(si, len(buckets) - 1)].append(DocxTable(child, doc))

        return list(zip(setups, buckets))

    def _extract_images(
        self,
        paragraph: DocxParagraph,
        doc: Document,
        media_dir: Path,
        index: int,
    ) -> Path | None:
        blips = paragraph._element.findall(".//" + _A_BLIP)
        if not blips:
            return None
        rid = blips[0].get(_R_EMBED)
        if not rid:
            return None
        try:
            part = doc.part.related_parts[rid]
        except KeyError:
            return None
        content_type = getattr(part, "content_type", "") or ""
        ext = ".bin"
        if "png" in content_type:
            ext = ".png"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"
        elif "emf" in content_type:
            ext = ".emf"
        elif "wmf" in content_type:
            ext = ".wmf"
        media_dir.mkdir(parents=True, exist_ok=True)
        dest = media_dir / f"image_{index + 1:03d}{ext}"
        try:
            dest.write_bytes(part.blob)
            return dest
        except Exception:
            return None

    def _read_table(self, table: DocxTable) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in table.rows:
            cells: list[str] = []
            seen_tc: set[int] = set()
            for cell in row.cells:
                tc_id = id(cell._tc)
                if tc_id in seen_tc:
                    continue
                seen_tc.add(tc_id)
                paras: list[str] = []
                for p in cell.paragraphs:
                    t = _paragraph_md_text(p).strip()
                    if t or not paras:
                        paras.append(t)
                text = "<br>".join(paras) if len(paras) > 1 else (paras[0] if paras else "")
                # soft line breaks (w:br) → \n; для MD-таблиц нужен <br>
                text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
                cells.append(text)
            rows.append(cells)
        return rows
