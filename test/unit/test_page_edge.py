"""Unit: edge cases PageSetup / parse_section_directive."""

from __future__ import annotations

from md2docx.domain.page import (
    PageSetup,
    page_setup_default,
    page_setup_from_physical,
    parse_section_directive_attrs,
)


def test_physical_without_hint_infers_landscape():
    s = page_setup_from_physical(297, 210)
    assert s.orientation == "landscape"
    assert s.width_mm <= s.height_mm


def test_physical_without_hint_portrait():
    s = page_setup_from_physical(210, 297)
    assert s.orientation == "portrait"


def test_parse_invalid_numbers_use_defaults():
    s = parse_section_directive_attrs(
        "orientation=portrait width_mm=notanumber margin_left=abc"
    )
    assert s.width_mm == 210.0
    assert s.margin_left_mm == 30.0


def test_parse_orient_alias():
    s = parse_section_directive_attrs("orient=land width_mm=210 height_mm=297")
    assert s.orientation == "landscape"


def test_differs_from_tolerance():
    a = page_setup_default()
    b = PageSetup(
        orientation="portrait",
        width_mm=210.2,
        height_mm=297.2,
        margin_left_mm=30.1,
        margin_right_mm=15.0,
        margin_top_mm=20.0,
        margin_bottom_mm=20.0,
    )
    assert not a.differs_from(b, tol=0.5)
    c = PageSetup(orientation="landscape")
    assert a.differs_from(c)


def test_physical_size_landscape_swaps():
    s = PageSetup(orientation="landscape", width_mm=210, height_mm=297)
    w, h = s.physical_size_mm()
    assert w > h
