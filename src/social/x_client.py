from __future__ import annotations

from src.models import SocialTrend
from src.social.base import SocialClient


class XClient(SocialClient):
    def __init__(self, bearer_token: str, queries: list[str]):
        self.bearer_token = bearer_token
        self.queries = queries

    def fetch_trends(self, limit: int = 10) -> list[SocialTrend]:
        return []
