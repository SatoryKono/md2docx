"""CLI inbound adapter — composition root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from md2docx.adapters.outbound.docx_reader import DocxReader
from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.json_style_repo import JsonStyleRepository
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.adapters.outbound.markdown_writer import MarkdownWriter
from md2docx.application.convert_docx import ConvertDocxToMarkdown
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.application.demo import BuildDemo
from md2docx.application.restyle import RestyleDocx
from md2docx.domain.errors import (
    InputNotFoundError,
    Md2DocxError,
    StyleConfigError,
    UnsupportedFormatError,
)
from md2docx.domain.model import TitleMeta
from md2docx.domain.stylespec import (
    BODY_PT,
    FIRST_LINE_MM,
    FONT,
    LINE_1_5,
    PAGE_DEFAULT,
    STYLE_NAMES,
    TABLE_PT,
    RenderOptions,
)


def _options_from_args(args: argparse.Namespace) -> RenderOptions:
    page = dict(PAGE_DEFAULT)
    if args.margin_left is not None:
        page["left_mm"] = args.margin_left
    if args.margin_right is not None:
        page["right_mm"] = args.margin_right
    if args.margin_top is not None:
        page["top_mm"] = args.margin_top
    if args.margin_bottom is not None:
        page["bottom_mm"] = args.margin_bottom

    font = args.font or FONT
    body_pt = BODY_PT if args.body_pt is None else args.body_pt
    table_pt = TABLE_PT if args.table_pt is None else args.table_pt
    line_spacing = LINE_1_5 if args.line_spacing is None else args.line_spacing
    first_line_mm = FIRST_LINE_MM
    style_pack = None

    if args.config:
        try:
            style_pack = JsonStyleRepository().load(args.config)
        except StyleConfigError:
            raise
        except Exception as exc:
            raise StyleConfigError(str(exc)) from exc
        font = args.font or style_pack.font
        if args.body_pt is None:
            body_pt = style_pack.body_pt
        if args.line_spacing is None:
            line_spacing = style_pack.line_spacing
        first_line_mm = style_pack.first_line_mm
        page = dict(style_pack.page)
        for key, cli in (
            ("left_mm", args.margin_left),
            ("right_mm", args.margin_right),
            ("top_mm", args.margin_top),
            ("bottom_mm", args.margin_bottom),
        ):
            if cli is not None:
                page[key] = cli
        if args.table_pt is None:
            table_pt = style_pack.table_pt

    return RenderOptions(
        font=font,
        body_pt=body_pt,
        table_pt=table_pt,
        line_spacing=line_spacing,
        first_line_mm=first_line_mm,
        page=page,
        page_numbers=not args.no_page_numbers,
        strict=bool(getattr(args, "strict", False)),
        style_pack=style_pack,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="md2docx",
        description=(
            "Markdown ↔ DOCX (ГОСТ 7.32–2017 / стили A.docx). "
            "Направление выбирается по расширениям -i/-o."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --demo -o report.docx
  %(prog)s -i chapter.md -o report.docx
  %(prog)s -i report.docx -o chapter.md
  %(prog)s -i draft.docx -o out.docx --restyle
        """,
    )
    io = p.add_argument_group("ввод / вывод")
    io.add_argument("-i", "--input", metavar="PATH")
    io.add_argument("-o", "--output", metavar="PATH", default=None)
    io.add_argument("--demo", action="store_true")
    io.add_argument(
        "--restyle",
        action="store_true",
        help="docx→docx: только стили ГОСТ (без конвертации в MD)",
    )
    io.add_argument(
        "--include-title",
        action="store_true",
        help="docx→md: включить YAML front matter с титулом",
    )
    io.add_argument(
        "--no-outline",
        action="store_true",
        help="docx→md: не пропускать преамбулу/TOC до раздела «1 …»",
    )
    io.add_argument(
        "--media-dir",
        metavar="PATH",
        help="docx→md: каталог для изображений (по умолчанию <stem>_media)",
    )

    fmt = p.add_argument_group("оформление")
    fmt.add_argument("--config", metavar="PATH")
    fmt.add_argument("--font", metavar="NAME")
    fmt.add_argument("--body-pt", type=float, metavar="N")
    fmt.add_argument("--table-pt", type=float, metavar="N")
    fmt.add_argument("--line-spacing", type=float, metavar="N")
    fmt.add_argument("--margin-left", type=float, metavar="MM")
    fmt.add_argument("--margin-right", type=float, metavar="MM")
    fmt.add_argument("--margin-top", type=float, metavar="MM")
    fmt.add_argument("--margin-bottom", type=float, metavar="MM")
    fmt.add_argument("--no-page-numbers", action="store_true")

    title = p.add_argument_group("титул (md→docx)")
    title.add_argument("--org", metavar="TEXT")
    title.add_argument("--topic", metavar="TEXT")
    title.add_argument("--city-year", metavar="TEXT")

    misc = p.add_argument_group("прочее")
    misc.add_argument("--list-styles", action="store_true")
    misc.add_argument(
        "--strict",
        action="store_true",
        help="ошибки медиа (отсутствующие картинки и т.п.) → non-zero exit",
    )
    misc.add_argument("-q", "--quiet", action="store_true")
    misc.add_argument("-v", "--verbose", action="store_true")
    return p


def default_output_for(input_path: str | None, demo: bool) -> str:
    if not input_path or demo:
        return "gost-demo.docx"
    p = Path(input_path)
    suf = p.suffix.lower()
    if suf in {".md", ".markdown", ".txt"}:
        return str(p.with_suffix(".docx"))
    if suf == ".docx":
        return str(p.with_suffix(".md"))
    return str(p.with_suffix(".docx"))


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_styles:
        for name in STYLE_NAMES:
            print(name)
        return 0

    try:
        options = _options_from_args(args)
        out = Path(args.output or default_output_for(args.input, args.demo))
        writer = DocxWriter()
        parser_md = SimpleMarkdownParser()
        reader = DocxReader(
            outline=not args.no_outline,
            media_dir=args.media_dir,
        )
        md_writer = MarkdownWriter()

        if args.verbose:
            print(f"output: {out}", file=sys.stderr)
            print(f"options: {options}", file=sys.stderr)

        if args.demo or not args.input:
            path = BuildDemo(writer).execute(out, options)
        else:
            in_path = Path(args.input)
            if not in_path.is_file():
                raise InputNotFoundError(f"файл не найден: {args.input}")
            in_suf = in_path.suffix.lower()
            out_suf = out.suffix.lower()

            if in_suf == ".docx" and args.restyle:
                path = RestyleDocx(writer).execute(in_path, out, options)
            elif in_suf == ".docx" and out_suf in {".md", ".markdown", ".txt", ""}:
                if out_suf == "":
                    out = out.with_suffix(".md")
                path = ConvertDocxToMarkdown(reader, md_writer).execute(
                    in_path,
                    out,
                    include_title=args.include_title,
                )
            elif in_suf in {".md", ".markdown", ".txt"}:
                if out_suf in {".md", ".markdown"}:
                    raise UnsupportedFormatError("для MD-входа укажите выход .docx")
                text = in_path.read_text(encoding="utf-8")
                title = TitleMeta(org=args.org, topic=args.topic, city_year=args.city_year)
                path = ConvertMarkdownToDocx(parser_md, writer).execute(
                    text, out, options, title=title
                )
            elif in_suf == ".docx":
                if out_suf == ".docx":
                    raise UnsupportedFormatError(
                        "docx→docx требует --restyle; для docx→md укажите -o file.md"
                    )
                path = ConvertDocxToMarkdown(reader, md_writer).execute(
                    in_path,
                    out if out_suf else out.with_suffix(".md"),
                    include_title=args.include_title,
                )
            else:
                raise UnsupportedFormatError(f"неподдерживаемый тип: {in_suf}")
    except Md2DocxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        return int(getattr(exc, "exit_code", 1) or 1)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        return 1

    if not args.quiet:
        print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
