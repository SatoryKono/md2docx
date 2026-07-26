"""CLI inbound adapter — composition root."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from md2docx.adapters.outbound.docx_writer import DocxWriter
from md2docx.adapters.outbound.markdown_parser import SimpleMarkdownParser
from md2docx.application.convert_md import ConvertMarkdownToDocx
from md2docx.application.demo import BuildDemo
from md2docx.application.restyle import RestyleDocx
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

    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        d = cfg.get("defaults", {})
        p = cfg.get("page", {})
        font = args.font or d.get("font", font)
        if args.body_pt is None:
            body_pt = d.get("body_size_pt", body_pt)
        if args.line_spacing is None:
            line_spacing = d.get("line_spacing", line_spacing)
        first_line_mm = d.get("first_line_indent_mm", first_line_mm)
        page = {
            "width_mm": p.get("width_mm", 210),
            "height_mm": p.get("height_mm", 297),
            "left_mm": p.get("margins_mm", {}).get("left", 30),
            "right_mm": p.get("margins_mm", {}).get("right", 15),
            "top_mm": p.get("margins_mm", {}).get("top", 20),
            "bottom_mm": p.get("margins_mm", {}).get("bottom", 20),
        }
        for key, cli in (
            ("left_mm", args.margin_left),
            ("right_mm", args.margin_right),
            ("top_mm", args.margin_top),
            ("bottom_mm", args.margin_bottom),
        ):
            if cli is not None:
                page[key] = cli
        if args.table_pt is None:
            for st in cfg.get("styles", []):
                if st.get("style_id") == "TableCell":
                    table_pt = st.get("run", {}).get("size_pt", table_pt)
                    break

    return RenderOptions(
        font=font,
        body_pt=body_pt,
        table_pt=table_pt,
        line_spacing=line_spacing,
        first_line_mm=first_line_mm,
        page=page,
        page_numbers=not args.no_page_numbers,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="md2docx",
        description="Markdown → DOCX (ГОСТ 7.32–2017 / стили A.docx).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s --demo -o report.docx
  %(prog)s -i chapter.md -o report.docx
  %(prog)s -i draft.docx -o report.docx --restyle
        """,
    )
    io = p.add_argument_group("ввод / вывод")
    io.add_argument("-i", "--input", metavar="PATH")
    io.add_argument("-o", "--output", metavar="PATH", default=None)
    io.add_argument("--demo", action="store_true")
    io.add_argument("--restyle", action="store_true")

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

    title = p.add_argument_group("титул")
    title.add_argument("--org", metavar="TEXT")
    title.add_argument("--topic", metavar="TEXT")
    title.add_argument("--city-year", metavar="TEXT")

    misc = p.add_argument_group("прочее")
    misc.add_argument("--list-styles", action="store_true")
    misc.add_argument("-q", "--quiet", action="store_true")
    misc.add_argument("-v", "--verbose", action="store_true")
    return p


def default_output_for(input_path: str | None, demo: bool) -> str:
    if input_path and not demo:
        return str(Path(input_path).with_suffix(".docx"))
    return "gost-demo.docx"


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_styles:
        for name in STYLE_NAMES:
            print(name)
        return 0

    options = _options_from_args(args)
    out = Path(args.output or default_output_for(args.input, args.demo))
    writer = DocxWriter()
    parser_md = SimpleMarkdownParser()

    if args.verbose:
        print(f"output: {out}", file=sys.stderr)
        print(f"options: {options}", file=sys.stderr)

    try:
        if args.demo or not args.input:
            path = BuildDemo(writer).execute(out, options)
        else:
            in_path = Path(args.input)
            if not in_path.is_file():
                print(f"error: файл не найден: {args.input}", file=sys.stderr)
                return 1
            suffix = in_path.suffix.lower()
            if suffix == ".docx":
                if not args.restyle:
                    print(
                        "error: для .docx укажите --restyle",
                        file=sys.stderr,
                    )
                    return 2
                path = RestyleDocx(writer).execute(in_path, out, options)
            elif suffix in {".md", ".markdown", ".txt"}:
                text = in_path.read_text(encoding="utf-8")
                title = TitleMeta(
                    org=args.org, topic=args.topic, city_year=args.city_year
                )
                path = ConvertMarkdownToDocx(parser_md, writer).execute(
                    text, out, options, title=title
                )
            else:
                print(
                    f"error: неподдерживаемый тип: {suffix}",
                    file=sys.stderr,
                )
                return 2
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
