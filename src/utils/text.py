from __future__ import annotations

import re
from html import unescape


def clean_html(raw_text: str) -> str:
    return unescape(re.sub(r"<.*?>", "", raw_text or "")).strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
