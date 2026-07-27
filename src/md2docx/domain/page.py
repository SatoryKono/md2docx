"""Параметры страницы / секции (ориентация, размер, поля)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Orientation = Literal["portrait", "landscape"]


@dataclass(frozen=True)
class PageSetup:
    """Логический размер: width/height как для portrait (короткая × длинная).

    orientation отдельно; при записи в Word для landscape width/height swap.
    """

    orientation: Orientation = "portrait"
    width_mm: float = 210.0
    height_mm: float = 297.0
    margin_left_mm: float = 30.0
    margin_right_mm: float = 15.0
    margin_top_mm: float = 20.0
    margin_bottom_mm: float = 20.0

    def normalized(self) -> PageSetup:
        """width ≤ height в logical portrait coords; mm округлены (stable MD)."""

        def r(x: float) -> float:
            return round(float(x), 1)

        w, h = self.width_mm, self.height_mm
        if w > h:
            w, h = h, w
        return PageSetup(
            orientation=self.orientation,
            width_mm=r(w),
            height_mm=r(h),
            margin_left_mm=r(self.margin_left_mm),
            margin_right_mm=r(self.margin_right_mm),
            margin_top_mm=r(self.margin_top_mm),
            margin_bottom_mm=r(self.margin_bottom_mm),
        )

    def physical_size_mm(self) -> tuple[float, float]:
        """(page_width, page_height) как в Word после учёта orientation."""
        n = self.normalized()
        if n.orientation == "landscape":
            return n.height_mm, n.width_mm
        return n.width_mm, n.height_mm

    def to_directive_attrs(self) -> str:
        n = self.normalized()
        parts = [
            f"orientation={n.orientation}",
            f"width_mm={n.width_mm:g}",
            f"height_mm={n.height_mm:g}",
            f"margin_left={n.margin_left_mm:g}",
            f"margin_right={n.margin_right_mm:g}",
            f"margin_top={n.margin_top_mm:g}",
            f"margin_bottom={n.margin_bottom_mm:g}",
        ]
        return " ".join(parts)

    def differs_from(self, other: PageSetup, *, tol: float = 0.5) -> bool:
        a, b = self.normalized(), other.normalized()
        if a.orientation != b.orientation:
            return True
        for x, y in (
            (a.width_mm, b.width_mm),
            (a.height_mm, b.height_mm),
            (a.margin_left_mm, b.margin_left_mm),
            (a.margin_right_mm, b.margin_right_mm),
            (a.margin_top_mm, b.margin_top_mm),
            (a.margin_bottom_mm, b.margin_bottom_mm),
        ):
            if abs(x - y) > tol:
                return True
        return False


def page_setup_default() -> PageSetup:
    return PageSetup()


def page_setup_from_physical(
    width_mm: float,
    height_mm: float,
    *,
    margin_left_mm: float = 30.0,
    margin_right_mm: float = 15.0,
    margin_top_mm: float = 20.0,
    margin_bottom_mm: float = 20.0,
    orientation_hint: Orientation | None = None,
) -> PageSetup:
    """Из физических размеров Word (page_width/page_height)."""
    if orientation_hint is not None:
        orient = orientation_hint
    else:
        orient = "landscape" if width_mm > height_mm + 0.5 else "portrait"
    logical_w, logical_h = min(width_mm, height_mm), max(width_mm, height_mm)
    return PageSetup(
        orientation=orient,
        width_mm=logical_w,
        height_mm=logical_h,
        margin_left_mm=margin_left_mm,
        margin_right_mm=margin_right_mm,
        margin_top_mm=margin_top_mm,
        margin_bottom_mm=margin_bottom_mm,
    ).normalized()


def parse_section_directive_attrs(attrs: str) -> PageSetup:
    """Parse 'orientation=landscape width_mm=297 ...'."""
    kv: dict[str, str] = {}
    for part in attrs.split():
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip().lower()] = v.strip()

    orient_raw = kv.get("orientation") or kv.get("orient") or "portrait"
    orient: Orientation = (
        "landscape" if orient_raw.lower().startswith("land") else "portrait"
    )

    def f(key: str, default: float) -> float:
        try:
            return float(kv.get(key, default))
        except (TypeError, ValueError):
            return default

    return PageSetup(
        orientation=orient,
        width_mm=f("width_mm", 210.0),
        height_mm=f("height_mm", 297.0),
        margin_left_mm=f("margin_left", f("margin_left_mm", 30.0)),
        margin_right_mm=f("margin_right", f("margin_right_mm", 15.0)),
        margin_top_mm=f("margin_top", f("margin_top_mm", 20.0)),
        margin_bottom_mm=f("margin_bottom", f("margin_bottom_mm", 20.0)),
    ).normalized()
