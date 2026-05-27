from __future__ import annotations

from pathlib import Path

from data_sources.cache_store import is_fresh, read_cache, response, write_cache
from data_sources.sample_provider import load_sample_news
from src.news_fetcher import NewsFetcher
from src.news_filters import filter_default_scope
from src.models import NewsArticle, article_field, article_to_dict


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

    live = refresh_news_response(
        fetcher=fetcher,
        sources=sources,
        data_dir=data_dir,
        newsapi_key=newsapi_key,
        serpapi_key=serpapi_key,
        newsdata_key=newsdata_key,
        limit=limit,
    )
    if any(live.get("data", {}).values()):
        return _deserialize_response(live, live.get("source", "live"), status=live.get("status"), message=live.get("message"))
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
        fetch_limit = max(limit * 3, 20)
        collected: list[NewsArticle | dict] = []
        for source_name, loader in [
            ("NewsAPI", lambda: fetcher.fetch_newsapi(newsapi_key, category, NEWS_QUERIES[category], fetch_limit)),
            ("SerpAPI", lambda: fetcher.fetch_serpapi_google_news(serpapi_key, category, NEWS_QUERIES[category], fetch_limit)),
            ("NewsData", lambda: fetcher.fetch_newsdata(newsdata_key, category, NEWS_QUERIES[category], fetch_limit)),
            ("RSS", lambda: fetcher.fetch_category(category, sources.get(category, []), fetch_limit)),
        ]:
            raw = loader()
            filtered = filter_default_scope(raw)
            print(f"[news-debug] {category}/{source_name}: raw={len(raw)}, filtered={len(filtered)}")
            collected.extend(filtered)
        deduped = _deduplicate_articles(collected)
        print(f"[news-debug] {category}/merged: raw={len(collected)}, deduped={len(deduped)}, final={len(deduped[:limit])}")
        grouped[category] = deduped[:limit]
        if not grouped[category]:
            sample_rows = load_sample_news(data_dir / "sample_news.json", category, limit)
            print(f"[news-debug] {category}/sample: raw={len(sample_rows)}, filtered={len(sample_rows)}")
            grouped[category] = sample_rows
    data = {category: [article_to_dict(article) for article in articles] for category, articles in grouped.items()}
    source = (
        "live"
        if any(article for articles in grouped.values() for article in articles if str(article_field(article, "source")).lower() not in {"离线样例", "sample"})
        else "sample"
    )
    try:
        payload = write_cache(data_dir / "cache" / "news_cache.json", data, source)
        if source == "sample":
            payload["status"] = "fallback"
            payload["message"] = "实时新闻暂不可用，已展示示例新闻。"
        return payload
    except OSError:
        return response("fallback", source, data, "实时新闻暂不可用，已展示示例新闻。")


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


def _deduplicate_articles(articles: list[NewsArticle | dict]) -> list[NewsArticle | dict]:
    seen: set[str] = set()
    result: list[NewsArticle | dict] = []
    for article in articles:
        title = str(article_field(article, "title", "")).strip()
        link = str(article_field(article, "link", "") or article_field(article, "url", "")).strip()
        key = link or title
        if key and key not in seen:
            seen.add(key)
            result.append(article)
    return result
