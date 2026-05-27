from __future__ import annotations

import types

from src.models import NewsArticle


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("bad status")

    def json(self) -> dict:
        return self._payload


def test_serpapi_google_news_results_convert_to_articles(monkeypatch):
    import src.news_fetcher as news_fetcher

    def fake_get(url, params, timeout):
        assert url == "https://serpapi.com/search.json"
        assert params["engine"] == "google_news"
        assert params["hl"] == "zh-cn"
        assert params["gl"] == "cn"
        return FakeResponse(
            {
                "news_results": [
                    {
                        "title": "中国资产重现股汇共振",
                        "snippet": "A股与人民币同步走强。",
                        "link": "https://example.com/a",
                        "date": "05/25/2026, 09:00 AM, +0800 UTC",
                        "source": {"name": "第一财经"},
                    }
                ]
            }
        )

    monkeypatch.setattr(news_fetcher.requests, "get", fake_get)

    articles = news_fetcher.NewsFetcher().fetch_serpapi_google_news("serp-key", "finance", "A股 人民币", 5)

    assert len(articles) == 1
    assert articles[0].title == "中国资产重现股汇共振"
    assert articles[0].source == "第一财经"
    assert articles[0].category == "finance"


def test_filter_news_removes_taiwan_items_by_default():
    from src.news_filters import filter_grouped_news

    grouped = {
        "politics": [
            NewsArticle("WHA 場外價值 醫籲台灣投資全球衛生外交培力", "台灣地方政治", "Yahoo", "", "", "politics"),
            NewsArticle("国务院部署稳增长政策", "中国大陆宏观政策继续发力", "新华社", "", "", "politics"),
        ]
    }

    filtered = filter_grouped_news(grouped, "")

    assert [article.title for article in filtered["politics"]] == ["国务院部署稳增长政策"]


def test_filter_news_keeps_taiwan_items_when_user_searches_taiwan():
    from src.news_filters import filter_grouped_news

    grouped = {
        "politics": [
            NewsArticle("WHA 場外價值 醫籲台灣投資全球衛生外交培力", "台灣地方政治", "Yahoo", "", "", "politics"),
            NewsArticle("国务院部署稳增长政策", "中国大陆宏观政策继续发力", "新华社", "", "", "politics"),
        ]
    }

    filtered = filter_grouped_news(grouped, "台湾")

    assert [article.title for article in filtered["politics"]] == ["WHA 場外價值 醫籲台灣投資全球衛生外交培力"]


def test_default_scope_filter_keeps_mainland_and_western_policy_news():
    from src.news_filters import filter_default_scope

    rows = [
        NewsArticle("擺脫低潮找回身手 道奇牛棚左投談去年表現", "MLB 赛况", "Yahoo Entertainment", "", "", "finance"),
        NewsArticle("第一财经：中国资产重现股汇共振", "A股与人民币同步走强", "第一财经", "", "", "finance"),
        NewsArticle("Fed signals cautious path as inflation stays sticky", "US economy watches rates", "Reuters", "", "", "finance"),
    ]

    filtered = filter_default_scope(rows)

    assert [article.title for article in filtered] == [
        "第一财经：中国资产重现股汇共振",
        "Fed signals cautious path as inflation stays sticky",
    ]


def test_get_news_falls_back_to_serpapi_when_newsapi_empty(monkeypatch, tmp_path):
    from data_sources.news_service import refresh_news_response

    calls: list[str] = []

    class FakeFetcher:
        def fetch_newsapi(self, api_key, category, query, limit):
            calls.append(f"newsapi:{category}")
            return [NewsArticle("道奇牛棚左投谈去年表现", "MLB 赛况", "Yahoo Entertainment", "", "", category)]

        def fetch_serpapi_google_news(self, api_key, category, query, limit):
            calls.append(f"serpapi:{category}")
            return [NewsArticle(f"{category} 欧美政治经济动态", "美联储和欧洲政策", "SerpAPI", "", "", category)]

        def fetch_newsdata(self, api_key, category, query, limit):
            calls.append(f"newsdata:{category}")
            return []

        def fetch_category(self, category, sources, limit):
            calls.append(f"rss:{category}")
            return []

        def load_sample_news(self, path, category=None, limit=10):
            calls.append(f"sample:{category}")
            return []

    payload = refresh_news_response(
        fetcher=FakeFetcher(),
        sources={"finance": [], "politics": [], "culture": []},
        data_dir=tmp_path,
        newsapi_key="news-key",
        serpapi_key="serp-key",
        newsdata_key="",
        limit=3,
    )
    grouped = payload["data"]

    assert grouped["finance"][0]["source"] == "SerpAPI"
    assert "newsapi:finance" in calls
    assert "serpapi:finance" in calls
    assert "rss:finance" not in calls
