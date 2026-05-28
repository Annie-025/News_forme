from __future__ import annotations

from src.models import SocialTrend
from src.social.base import SocialClient


class RedditClient(SocialClient):
    def __init__(self, client_id: str, client_secret: str, user_agent: str, subreddits: list[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.subreddits = subreddits

    def fetch_trends(self, limit: int = 10) -> list[SocialTrend]:
        return []
