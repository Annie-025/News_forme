from __future__ import annotations

from pathlib import Path

from data_sources.cache_store import is_fresh, read_cache, response, write_cache
from data_sources.sample_provider import load_sample_news
from src.news_fetcher import NewsFetcher
from src.news_filters import filter_default_scope
from src.models import NewsArticle


NEWS_QUERIES = {
    "finance": "(A股 OR 人民币 OR 中国经济 OR 中国资产 OR 欧美经济 OR 美联储 OR 欧央行 OR 美元 OR 通胀 OR 能源) -台湾 -台灣 -Taiwan",
    "politics": "(中国大陆政策 OR 宏观政策 OR 美国政治 OR 欧洲政治 OR 地缘政治 OR 贸易政策) -台湾 -台灣 -Taiwan",
    "culture": "(文旅消费 OR 中国消费 OR 文化产业 OR 电影市场 OR 音乐产业) -台湾 -台灣 -Taiwan",
}


def get_news_response(
    *,
    fetcher: NewsFetcher,
    sources: dict,
    data_dir: Path,
    newsapi_key: str,
    serpapi_key: str,
    newsdata_key: str,
    limit: int,
    ttl_seconds: int = 600,
) -> dict:
    cache_path = data_dir / "cache" / "news_cache.json"
    sample_path = data_dir / "sample_news.json"
    cached = read_cache(cache_path)
    if is_fresh(cached, ttl_seconds):
        return _deserialize_response(cached, "cache")
    if cached:
        return _deserialize_response(cached, "cache", status="fallback", message="实时新闻暂不可用，已展示缓存。")

    sample = _sample_grouped(sample_path, limit)
    if any(sample.values()):
        return response("fallback", "sample", sample, "实时新闻暂不可用，已展示示例新闻。")
    return response("error", "empty", {"finance": [], "politics": [], "culture": []}, "暂无可用新闻。")


def refresh_news_response(
    *,
    fetcher: NewsFetcher,
    sources: dict,
    data_dir: Path,
    newsapi_key: str,
    serpapi_key: str,
    newsdata_key: str,
    limit: int,
) -> dict:
    grouped = {}
    for category in ["finance", "politics", "culture"]:
        articles = filter_default_scope(fetcher.fetch_newsapi(newsapi_key, category, NEWS_QUERIES[category], limit))
        if not articles:
            articles = filter_default_scope(fetcher.fetch_serpapi_google_news(serpapi_key, category, NEWS_QUERIES[category], limit))
        if not articles:
            articles = filter_default_scope(fetcher.fetch_newsdata(newsdata_key, category, NEWS_QUERIES[category], limit))
        if not articles:
            articles = filter_default_scope(fetcher.fetch_category(category, sources.get(category, []), limit))
        grouped[category] = articles
    data = {category: [article.to_dict() for article in articles] for category, articles in grouped.items()}
    return write_cache(data_dir / "cache" / "news_cache.json", data, "cache")


def _sample_grouped(sample_path: Path, limit: int) -> dict:
    return {
        category: load_sample_news(sample_path, category, limit)
        for category in ["finance", "politics", "culture"]
    }


def _deserialize_response(payload: dict, source: str, status: str | None = None, message: str | None = None) -> dict:
    data = payload.get("data") or {}
    grouped = {
        category: [NewsArticle.from_dict(row) for row in rows]
        for category, rows in data.items()
    }
    return response(status or payload.get("status", "success"), source, grouped, message or payload.get("message", ""), payload.get("updated_at"))
