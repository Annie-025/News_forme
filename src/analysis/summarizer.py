from __future__ import annotations

import re


def summarize(text: str, num_sentences: int = 2) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[。！？.!?])", text or "") if part.strip()]
    return "".join(sentences[:num_sentences])
