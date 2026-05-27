from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import SocialTrend


class SocialClient(ABC):
    @abstractmethod
    def fetch_trends(self, limit: int = 10) -> list[SocialTrend]:
        raise NotImplementedError
