from __future__ import annotations

from datetime import datetime

from dateutil import parser


def friendly_date(value: str) -> str:
    if not value:
        return ""
    try:
        return parser.parse(value).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError):
        return value


def parse_friendly_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
