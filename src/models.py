from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|bearer|password)=([^&\s]+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([^\s]+)"),
]


def sanitize_message(message: str) -> str:
    text = str(message or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:220]


@dataclass(frozen=True)
class SourceStatus:
    name: str
    configured: bool
    status: str
    message: str
    updated_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", sanitize_message(self.message))


@dataclass(frozen=True)
class MarketIndex:
    symbol: str
    name: str
    region: str
    price: float | None
    change: float | None
    change_pct: float | None
    turnover: float | None
    source: str
    updated_at: datetime | None
    status: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", sanitize_message(self.message))

    @property
    def ticker(self) -> str:
        return self.symbol

    @property
    def value(self) -> float | None:
        return self.price

    @property
    def updated_at_text(self) -> str:
        return self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else "未知"


@dataclass(frozen=True)
class AkShareSnapshot:
    updated_at: datetime | None
    a_spot_top: list[dict[str, Any]] = field(default_factory=list)
    index_spot: list[dict[str, Any]] = field(default_factory=list)
    limit_up_pool: list[dict[str, Any]] = field(default_factory=list)
    concept_boards: list[dict[str, Any]] = field(default_factory=list)
    fund_flow: list[dict[str, Any]] = field(default_factory=list)
    market_activity: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_status: list[SourceStatus] = field(default_factory=list)

    @property
    def updated_at_text(self) -> str:
        return self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else "未知"


@dataclass(frozen=True)
class NewsArticle:
    title: str
    content: str
    source: str = ""
    date: str = ""
    link: str = ""
    category: str = "finance"
    id: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    sentiment: str = "中性"
    impact: str = "中性"
    published_at: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary or self.content,
            "source": self.source,
            "date": self.date,
            "link": self.link,
            "category": self.category,
            "tags": self.tags,
            "sentiment": self.sentiment,
            "impact": self.impact,
            "published_at": self.published_at or self.date,
            "url": self.url or self.link,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "NewsArticle":
        summary = str(row.get("summary", row.get("content", "")))
        published_at = str(row.get("published_at", row.get("date", "")))
        url = str(row.get("url", row.get("link", "")))
        return cls(
            str(row.get("title", "")),
            str(row.get("content", summary)),
            str(row.get("source", "")),
            str(row.get("date", published_at[:10])),
            str(row.get("link", url)),
            str(row.get("category", "finance")),
            str(row.get("id", "")),
            summary,
            list(row.get("tags", [])),
            str(row.get("sentiment", "中性")),
            str(row.get("impact", "中性")),
            published_at,
            url,
        )


def article_field(article: NewsArticle | dict[str, Any], field: str, default: Any = "") -> Any:
    if isinstance(article, dict):
        value = article.get(field, default)
    else:
        value = getattr(article, field, default)
    if value is None:
        return default
    return value


def article_to_dict(article: NewsArticle | dict[str, Any]) -> dict[str, Any]:
    if isinstance(article, dict):
        return article
    return article.to_dict()


@dataclass(frozen=True)
class SocialTrend:
    platform: str
    topic: str
    summary: str
    keywords: list[str]
    heat: int
    url: str = ""
