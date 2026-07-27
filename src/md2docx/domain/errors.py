"""Типизированные ошибки; CLI маппит exit_code."""

from __future__ import annotations


class Md2DocxError(Exception):
    """Базовая ошибка md2docx."""

    exit_code: int = 1

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class InputNotFoundError(Md2DocxError):
    exit_code = 1


class UnsupportedFormatError(Md2DocxError):
    exit_code = 2


class MediaError(Md2DocxError):
    """Проблема с изображением/медиа."""

    exit_code = 1


class StyleConfigError(Md2DocxError):
    exit_code = 3


class WriteError(Md2DocxError):
    exit_code = 1


class ParseError(Md2DocxError):
    exit_code = 1
