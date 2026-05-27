from __future__ import annotations

from src.models import NewsArticle


class WorldBankDocumentsClient:
    def fetch_latest(self, limit: int = 5, query: str = "economic update") -> list[NewsArticle]:
        return []
