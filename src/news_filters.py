from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.analysis.news_analyzer import AnalyzedNews
from src.models import NewsArticle
from src.utils.time import parse_friendly_date


TAIWAN_TERMS = ("台湾", "台灣", "taiwan")
TAIWAN_LOCAL_TERMS = (
    "台湾",
    "台灣",
    "臺灣",
    "台北",
    "臺北",
    "台南",
    "臺南",
    "台东",
    "臺東",
    "高雄",
    "屏東",
    "屏东",
    "民進黨",
    "国民党",
    "國民黨",
    "赖清德",
    "賴清德",
    "台国安局",
    "台國安局",
    ".com.tw",
)

CATEGORY_TERMS = {
    "财经": ("市场", "财经", "人民币", "股市", "债市", "中国资产"),
    "宏观": ("宏观", "央行", "利率", "通胀", "财政", "政策"),
    "A股": ("A股", "创业板", "上证", "深证", "半导体", "芯片"),
    "美股": ("美股", "Fed", "美联储", "纳斯达克", "标普", "美元"),
    "科技": ("科技", "AI", "半导体", "芯片", "HBM", "产业链"),
    "政策": ("政策", "国务院", "发改委", "监管", "财政"),
    "产业": ("产业", "消费", "能源", "制造", "文旅", "供应链"),
    "国际": ("国际", "欧洲", "美国", "贸易", "地缘政治", "欧盟"),
}

DEFAULT_SCOPE_TERMS = (
    "a股",
    "中国经济",
    "中國經濟",
    "中国资产",
    "中國資產",
    "人民币",
    "人民幣",
    "国务院",
    "國務院",
    "央行",
    "发改委",
    "發改委",
    "商务部",
    "商務部",
    "上交所",
    "深交所",
    "港股",
    "半导体",
    "半導體",
    "芯片",
    "宏观",
    "宏觀",
    "股市",
    "债市",
    "債市",
    "财政",
    "財政",
    "货币政策",
    "貨幣政策",
    "美联储",
    "fed",
    "欧央行",
    "歐央行",
    "ecb",
    "美国经济",
    "美國經濟",
    "美国政治",
    "美國政治",
    "欧洲政治",
    "歐洲政治",
    "欧洲经济",
    "歐洲經濟",
    "欧盟",
    "歐盟",
    "美元指数",
    "美元指數",
    "美元兑",
    "美元兌",
    "美元汇率",
    "美元匯率",
    "通胀",
    "通膨",
    "能源",
    "贸易",
    "貿易",
    "关税",
    "關稅",
    "地缘政治",
    "地緣政治",
    "文旅消费",
    "文化产业",
    "文化產業",
)


@dataclass(frozen=True)
class NewsFilterRequest:
    category: str = "全部"
    keyword: str = ""
    sentiment: str = "全部"
    time_range: str = "全部"


def filter_grouped_news(grouped_news: dict, keyword: str) -> dict:
    allow_taiwan = has_taiwan_intent(keyword)
    return {
        category: [article for article in articles if _article_matches(article, keyword, allow_taiwan)]
        for category, articles in grouped_news.items()
    }


def filter_analyzed_news(items: list[AnalyzedNews], request: NewsFilterRequest) -> list[AnalyzedNews]:
    return [item for item in items if _matches_category(item, request.category) and _matches_keyword(item, request.keyword) and _matches_sentiment(item, request.sentiment) and _matches_time(item, request.time_range)]


def filter_default_scope(articles: list[NewsArticle]) -> list[NewsArticle]:
    return [article for article in articles if is_default_scope_article(article)]


def has_taiwan_intent(keyword: str) -> bool:
    lowered = (keyword or "").lower()
    return any(term in lowered for term in TAIWAN_TERMS)


def _article_field(article, field: str, default: str = "") -> str:
    """
    兼容两种新闻数据格式：
    1. NewsArticle 对象：article.title
    2. dict 字典：article["title"]
    """
    if isinstance(article, dict):
        value = article.get(field, default)
    else:
        value = getattr(article, field, default)

    if value is None:
        return default

    return str(value)


def is_taiwan_local_article(article: NewsArticle | dict) -> bool:
    text = "\n".join(
        [
            _article_field(article, "title"),
            _article_field(article, "content"),
            _article_field(article, "summary"),
            _article_field(article, "source"),
        ]
    ).lower()

    return any(term.lower() in text for term in TAIWAN_LOCAL_TERMS)


def _article_matches(article: NewsArticle | dict, keyword: str, allow_taiwan: bool) -> bool:
    if not allow_taiwan and is_taiwan_local_article(article):
        return False

    if not keyword:
        return True

    text = "\n".join(
        [
            _article_field(article, "title"),
            _article_field(article, "content"),
            _article_field(article, "summary"),
            _article_field(article, "source"),
        ]
    ).lower()

    if allow_taiwan and is_taiwan_local_article(article):
        return True

    return keyword.lower() in text


def is_default_scope_article(article: NewsArticle) -> bool:
    if is_taiwan_local_article(article):
        return False
    text = "\n".join(
        [
            _article_field(article, "title"),
            _article_field(article, "content"),
            _article_field(article, "summary"),
            _article_field(article, "source"),
        ]
    ).lower()
    return any(term.lower() in text for term in DEFAULT_SCOPE_TERMS)


def _matches_category(item: AnalyzedNews, category: str) -> bool:
    if category == "全部":
        return True
    text = _search_text(item)
    terms = CATEGORY_TERMS.get(category, (category,))
    return any(term.lower() in text for term in terms)


def _matches_keyword(item: AnalyzedNews, keyword: str) -> bool:
    if not keyword:
        return True
    return keyword.lower() in _search_text(item)


def _matches_sentiment(item: AnalyzedNews, sentiment: str) -> bool:
    if sentiment == "全部":
        return True
    if sentiment == "利好":
        return item.impact_direction == "偏利好"
    if sentiment == "利空":
        return item.impact_direction == "偏谨慎"
    if sentiment == "中性":
        return item.impact_direction == "不确定"
    if sentiment == "高影响":
        return item.impact_score >= 30
    if sentiment == "待分析":
        return item.impact_score <= 15
    return True


def _matches_time(item: AnalyzedNews, time_range: str) -> bool:
    if time_range == "全部" or not _article_field(item.article, "date", None):
        return True
    parsed = parse_friendly_date(_article_field(item.article, "date", None))
    if parsed is None:
        return False
    days = {"今日": 0, "近 3 天": 3, "近 7 天": 7}.get(time_range)
    if days is None:
        return True
    today = datetime.now().date()
    if days == 0:
        return parsed.date() == today
    return parsed.date() >= today - timedelta(days=days)


def _search_text(item: AnalyzedNews) -> str:
    article = item.article
    parts = [
        _article_field(article, "title"),
        _article_field(article, "content"),
        _article_field(article, "summary"),
        _article_field(article, "source"),
        _article_field(article, "category"),
        item.content_category,
        item.impact_direction,
        " ".join(item.display_tags),
        " ".join(item.impact_targets),
    ]
    return "\n".join(parts).lower()
