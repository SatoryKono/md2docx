"""StyleRepository: JSON → StylePack."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from md2docx.domain.errors import StyleConfigError
from md2docx.domain.stylespec import (
    BODY_PT,
    FIRST_LINE_MM,
    FONT,
    LINE_1_5,
    PAGE_DEFAULT,
    SMALL_PT,
    TABLE_PT,
    StylePack,
)


def _default_json_path() -> Path:
    # package data
    try:
        ref = resources.files("md2docx").joinpath("config/gost-7.32-2017-styles.json")
        with resources.as_file(ref) as p:
            return Path(p)
    except Exception:
        return Path(__file__).resolve().parents[2] / "config" / "gost-7.32-2017-styles.json"


class JsonStyleRepository:
    def load(self, path: Path | str | None = None) -> StylePack:
        p = Path(path) if path else _default_json_path()
        if not p.is_file():
            if path is None:
                return StylePack(source="code-defaults")
            raise StyleConfigError(f"style config not found: {p}")
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StyleConfigError(f"invalid style JSON: {p}: {exc}") from exc

        d = raw.get("defaults") or {}
        page_raw = raw.get("page") or {}
        margins = page_raw.get("margins_mm") or {}
        page = {
            "width_mm": float(page_raw.get("width_mm", PAGE_DEFAULT["width_mm"])),
            "height_mm": float(page_raw.get("height_mm", PAGE_DEFAULT["height_mm"])),
            "left_mm": float(margins.get("left", PAGE_DEFAULT["left_mm"])),
            "right_mm": float(margins.get("right", PAGE_DEFAULT["right_mm"])),
            "top_mm": float(margins.get("top", PAGE_DEFAULT["top_mm"])),
            "bottom_mm": float(margins.get("bottom", PAGE_DEFAULT["bottom_mm"])),
        }
        table_pt = TABLE_PT
        for st in raw.get("styles") or []:
            if st.get("style_id") == "TableCell":
                table_pt = float((st.get("run") or {}).get("size_pt", table_pt))
                break

        return StylePack(
            font=str(d.get("font", FONT)),
            body_pt=float(d.get("body_size_pt", BODY_PT)),
            table_pt=table_pt,
            small_pt=float(d.get("body_size_pt", SMALL_PT)),
            line_spacing=float(d.get("line_spacing", LINE_1_5)),
            first_line_mm=float(d.get("first_line_indent_mm", FIRST_LINE_MM)),
            page=page,
            styles=list(raw.get("styles") or []),
            source=str(p),
        )
