from __future__ import annotations

from src.models import SocialTrend
from src.social.base import SocialClient


class InstagramClient(SocialClient):
    def __init__(self, access_token: str, ig_user_id: str, hashtags: list[str], graph_version: str = "v25.0"):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.hashtags = hashtags
        self.graph_version = graph_version

    def fetch_trends(self, limit: int = 10) -> list[SocialTrend]:
        return []
