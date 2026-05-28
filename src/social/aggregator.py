from __future__ import annotations

from src.models import SocialTrend
from src.social.base import SocialClient


def collect_trends(clients: list[SocialClient], limit: int = 10) -> list[SocialTrend]:
    trends: list[SocialTrend] = []
    for client in clients:
        trends.extend(client.fetch_trends(limit=limit))
    return sorted(trends, key=lambda item: item.heat, reverse=True)[:limit]
