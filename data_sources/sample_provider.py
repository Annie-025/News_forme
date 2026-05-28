from __future__ import annotations

import json
from pathlib import Path

from src.models import NewsArticle


def load_sample_news(path: Path, category: str | None = None, limit: int | None = None) -> list[NewsArticle]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    articles = [NewsArticle.from_dict(row) for row in rows]
    if category:
        articles = [article for article in articles if article.category == category]
    return articles[:limit] if limit else articles
