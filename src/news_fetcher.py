from __future__ import annotations

from pathlib import Path
from typing import Iterable

import requests

try:
    import feedparser
except ImportError:
    feedparser = None

from src.models import NewsArticle, article_field
from data_sources.sample_provider import load_sample_news as load_sample_news_rows
from src.utils.text import clean_html, normalize_text
from src.utils.time import friendly_date


class NewsFetcher:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_category(self, category: str, sources: Iterable[dict], limit: int) -> list[NewsArticle]:
        articles: list[NewsArticle] = []
        for source in sources:
            articles.extend(self._fetch_rss(source, category, limit))
        return self._deduplicate(articles)[:limit]

    def fetch_newsapi(self, api_key: str, category: str, query: str, limit: int) -> list[NewsArticle]:
        if not api_key:
            return []
        params = {
            "apiKey": api_key,
            "q": query,
            "searchIn": "title,description,content",
            "language": "zh",
            "sortBy": "publishedAt",
            "pageSize": limit,
        }
        try:
            response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []
        return [
            NewsArticle(
                normalize_text(item.get("title") or "无标题"),
                clean_html(item.get("description") or item.get("content") or item.get("title") or ""),
                (item.get("source") or {}).get("name") or "NewsAPI",
                friendly_date(item.get("publishedAt") or ""),
                item.get("url") or "",
                category,
            )
            for item in payload.get("articles", [])[:limit]
        ]

    def fetch_serpapi_google_news(self, api_key: str, category: str, query: str, limit: int) -> list[NewsArticle]:
        if not api_key:
            return []
        params = {
            "engine": "google_news",
            "q": query,
            "hl": "zh-cn",
            "gl": "cn",
            "num": limit,
            "api_key": api_key,
        }
        try:
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []
        articles: list[NewsArticle] = []
        for item in payload.get("news_results", [])[:limit]:
            source = item.get("source") or {}
            source_name = source.get("name") if isinstance(source, dict) else str(source)
            articles.append(
                NewsArticle(
                    normalize_text(item.get("title") or "无标题"),
                    clean_html(item.get("snippet") or item.get("summary") or item.get("title") or ""),
                    source_name or "SerpAPI Google News",
                    friendly_date(item.get("date") or ""),
                    item.get("link") or "",
                    category,
                )
            )
        return articles

    def fetch_newsdata(self, api_key: str, category: str, query: str, limit: int) -> list[NewsArticle]:
        return []

    def load_sample_news(self, path: Path, category: str | None = None, limit: int = 10) -> list[NewsArticle]:
        return load_sample_news_rows(path, category, limit)

    def _fetch_rss(self, source: dict, category: str, limit: int) -> list[NewsArticle]:
        if not feedparser or not source.get("url"):
            return []
        try:
            response = requests.get(source["url"], timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            return []
        feed = feedparser.parse(response.content)
        return [
            NewsArticle(
                normalize_text(getattr(item, "title", "无标题")),
                clean_html(getattr(item, "summary", "")) or normalize_text(getattr(item, "title", "无标题")),
                source.get("name", "RSS"),
                friendly_date(getattr(item, "published", "")),
                getattr(item, "link", ""),
                category,
            )
            for item in feed.entries[:limit]
        ]

    def _deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        return self.deduplicate_articles(articles)

    def deduplicate_articles(self, articles: list[NewsArticle | dict]) -> list[NewsArticle | dict]:
        seen: set[str] = set()
        result: list[NewsArticle | dict] = []
        for article in articles:
            title = article_field(article, "title")
            link = article_field(article, "link") or article_field(article, "url")
            key = (link or title).strip()
            if key and key not in seen:
                seen.add(key)
                result.append(article)
        return result
