from __future__ import annotations

from datetime import datetime, timedelta

from src.models import NewsArticle


def test_cache_payload_uses_fresh_cache_before_loader(tmp_path):
    from src.cache_store import load_or_refresh_json

    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        '{"updated_at":"2026-05-26T10:00:00","data":{"items":[1]},"status":"success","source":"cache"}',
        encoding="utf-8",
    )
    calls = {"loader": 0}

    def loader():
        calls["loader"] += 1
        return {"items": [2]}, "live"

    payload = load_or_refresh_json(cache_path, ttl_seconds=600, loader=loader, now=datetime(2026, 5, 26, 10, 5))

    assert calls["loader"] == 0
    assert payload["source"] == "cache"
    assert payload["data"] == {"items": [1]}


def test_cache_payload_falls_back_to_stale_cache_when_loader_fails(tmp_path):
    from src.cache_store import load_or_refresh_json

    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        '{"updated_at":"2026-05-26T09:00:00","data":{"items":[1]},"status":"success","source":"cache"}',
        encoding="utf-8",
    )

    def loader():
        raise RuntimeError("network exploded with token=secret")

    payload = load_or_refresh_json(cache_path, ttl_seconds=60, loader=loader, now=datetime(2026, 5, 26, 10, 5))

    assert payload["source"] == "cache"
    assert payload["status"] == "fallback"
    assert payload["data"] == {"items": [1]}
    assert "secret" not in payload["message"]


def test_news_filter_request_supports_category_keyword_sentiment_and_time():
    from src.news_filters import NewsFilterRequest, filter_analyzed_news
    from src.analysis.news_analyzer import analyze_news_items

    today = datetime.now().strftime("%Y-%m-%d")
    rows = analyze_news_items(
        [
            NewsArticle("A股半导体走强", "芯片产业链景气改善", "财媒", today, "", "finance"),
            NewsArticle("海外体育新闻", "赛事回顾", "体育源", "2024-01-01", "", "culture"),
        ]
    )

    filtered = filter_analyzed_news(
        rows,
        NewsFilterRequest(category="A股", keyword="半导体", sentiment="利好", time_range="今日"),
    )

    assert len(filtered) == 1
    assert filtered[0].article.title == "A股半导体走强"


def test_analyzed_news_card_does_not_render_ai_until_button_clicked(monkeypatch):
    import src.ui.market_dashboard_page as page
    from src.analysis.news_analyzer import analyze_news_item

    item = analyze_news_item(NewsArticle("央行释放流动性", "利率政策影响市场", "财媒", "2026-05-26", "", "finance"))
    rendered: list[str] = []
    monkeypatch.setattr(page.st, "markdown", lambda body, **kwargs: rendered.append(body))
    monkeypatch.setattr(page.st, "button", lambda *args, **kwargs: False)

    page.render_analyzed_news_card(item)

    html = "\n".join(rendered)
    assert "AI 解读" not in html
    assert "ai-card" not in html


def test_news_response_uses_sample_without_akshare(tmp_path, monkeypatch):
    import json
    import sys

    from data_sources.news_service import get_news_response
    from src.news_fetcher import NewsFetcher

    sample_path = tmp_path / "sample_news.json"
    rows = [
        {
            "id": "s1",
            "title": "A股样例新闻",
            "summary": "样例摘要",
            "source": "sample",
            "category": "finance",
            "tags": ["A股"],
            "sentiment": "中性",
            "impact": "中性",
            "published_at": "2026-05-26T09:00:00+08:00",
            "url": "mock://sample",
        }
    ]
    sample_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setitem(sys.modules, "akshare", None)

    payload = get_news_response(
        fetcher=NewsFetcher(),
        sources={},
        data_dir=tmp_path,
        newsapi_key="",
        serpapi_key="",
        newsdata_key="",
        limit=5,
    )

    assert payload["source"] == "sample"
    assert payload["status"] == "fallback"
    assert payload["data"]["finance"][0].title == "A股样例新闻"


def test_market_response_returns_empty_when_provider_and_cache_fail(tmp_path, monkeypatch):
    import src.market.market_service as market_service

    monkeypatch.setattr(market_service, "fetch_market_indices", lambda: [])

    class EmptySnapshot:
        a_spot_top = []
        index_spot = []
        concept_boards = []
        fund_flow = []
        market_activity = []
        limit_up_pool = []

    monkeypatch.setattr(market_service, "fetch_akshare_snapshot", lambda limit=8: EmptySnapshot())

    payload = market_service.get_market_response(tmp_path, ttl_seconds=0)

    assert payload["status"] == "fallback"
    assert payload["source"] == "empty"
    assert len(payload["data"]["indices"]) >= 5
    assert payload["data"]["snapshot"] is None


def test_market_response_is_available_from_new_market_package(tmp_path, monkeypatch):
    import src.market.market_service as market_service

    monkeypatch.setattr(market_service, "fetch_market_indices", lambda: [])

    class EmptySnapshot:
        a_spot_top = []
        index_spot = []
        concept_boards = []
        fund_flow = []
        market_activity = []
        limit_up_pool = []

    monkeypatch.setattr(market_service, "fetch_akshare_snapshot", lambda limit=8: EmptySnapshot())

    payload = market_service.get_market_response(tmp_path, ttl_seconds=0)

    assert payload["data"]["indices"]
    assert payload["status"] == "fallback"
