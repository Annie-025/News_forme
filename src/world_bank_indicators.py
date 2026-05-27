from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorldBankIndicator:
    indicator_name: str
    indicator_code: str
    country: str
    latest_value: float | None
    latest_observation_year: int | None
    freshness_status: str
    database_updated_at: str
    explanation: str
    theme: str

    @property
    def is_core_dashboard_eligible(self) -> bool:
        return self.latest_observation_year is not None and datetime.now().year - self.latest_observation_year <= 5


class WorldBankIndicatorsClient:
    def fetch_indicators(self, country: str = "CHN") -> list[WorldBankIndicator]:
        return []


def dashboard_eligible_indicators(indicators: list[WorldBankIndicator], limit: int = 3) -> list[WorldBankIndicator]:
    return [indicator for indicator in indicators if indicator.is_core_dashboard_eligible][:limit]
