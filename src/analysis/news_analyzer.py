from __future__ import annotations

from dataclasses import dataclass

from src.analysis.summarizer import summarize
from src.models import NewsArticle


@dataclass(frozen=True)
class AnalyzedNews:
    article: NewsArticle | dict
    content_category: str
    display_tags: list[str]
    impact_targets: list[str]
    impact_direction: str
    impact_score: int
    ai_analysis: dict[str, str]


KEYWORD_RULES = [
    (["央行", "利率", "降息", "加息", "通胀", "Fed"], 28, "宏观", ["A股", "港股", "人民币"], "偏谨慎"),
    (["人民币", "汇率", "美元"], 18, "市场", ["人民币", "港股"], "不确定"),
    (["消费", "文旅", "retail"], 14, "消费", ["消费", "A股"], "偏利好"),
    (["半导体", "芯片", "AI"], 18, "公司", ["科技", "创业板"], "偏利好"),
]


def analyze_news_items(articles: list[NewsArticle | dict]) -> list[AnalyzedNews]:
    return sorted([analyze_news_item(article) for article in articles], key=lambda item: item.impact_score, reverse=True)


def _article_field(article, field: str, default=None):
    if isinstance(article, dict):
        return article.get(field, default)

    return getattr(article, field, default)


def preview_news_items(articles: list[NewsArticle | dict]) -> list[AnalyzedNews]:
    return sorted([preview_news_item(article) for article in articles], key=lambda item: item.impact_score, reverse=True)


def preview_news_item(article: NewsArticle | dict) -> AnalyzedNews:
    title = _article_field(article, "title", "无标题")
    summary = _article_field(article, "summary", "")
    content = _article_field(article, "content", "")
    category = _article_field(article, "category", "finance")
    sentiment = _article_field(article, "sentiment", "中性")
    impact = _article_field(article, "impact", "中性")
    tags = _article_field(article, "tags", None)

    direction = {"利好": "偏利好", "利空": "偏谨慎", "中性": "不确定"}.get(sentiment, sentiment or "不确定")
    score = 38 if impact == "高影响" else 18
    tags = tags or [_default_category(category), direction, _time_badge(article)]
    targets = [tag for tag in tags if tag in ["A股", "美股", "科技", "政策", "宏观", "产业", "国际"]] or ["整体市场"]

    return AnalyzedNews(
        article=article,
        content_category=_default_category(category),
        display_tags=tags,
        impact_targets=targets,
        impact_direction=direction,
        impact_score=score,
        ai_analysis={
            "事实摘要": summary or content or title,
            "经济学机制": "",
            "可能影响": "",
            "不确定性": "",
        },
    )


def analyze_news_item(article: NewsArticle | dict) -> AnalyzedNews:
    title = _article_field(article, "title", "无标题")
    content = _article_field(article, "content", "")
    summary = _article_field(article, "summary", "")
    raw_category = _article_field(article, "category", "finance")
    date = _article_field(article, "date", None) or _article_field(article, "published_at", None)

    text = f"{title}\n{content}\n{summary}".lower()
    score = 8
    category = _default_category(raw_category)
    targets: set[str] = set()
    directions: list[str] = []

    for keywords, weight, rule_category, rule_targets, direction in KEYWORD_RULES:
        if any(keyword.lower() in text for keyword in keywords):
            score += weight
            category = rule_category
            targets.update(rule_targets)
            directions.append(direction)

    if date:
        score += 5

    direction = _direction(directions)
    targets_list = sorted(targets) or ["整体市场"]

    return AnalyzedNews(
        article=article,
        content_category=category,
        display_tags=[category, direction, _time_badge(article)],
        impact_targets=targets_list,
        impact_direction=direction,
        impact_score=min(score, 100),
        ai_analysis={
            "事实摘要": summarize(content or summary, 1) or title,
            "经济学机制": f"该信息可能通过政策预期、资金流和风险偏好影响{'、'.join(targets_list)}。",
            "可能影响": f"方向为{direction}，这是规则推断，不构成投资建议。",
            "不确定性": "需继续观察官方数据、成交量和后续政策细节。",
        },
    )


def market_sentiment(indices_change: list[float | None], analyzed_news: list[AnalyzedNews]) -> tuple[str, str]:
    valid = [change for change in indices_change if change is not None]
    positive = sum(1 for change in valid if change > 0)
    negative = sum(1 for change in valid if change < 0)
    if negative > positive:
        return "偏谨慎", "成功获取的主要指数偏弱，市场情绪偏谨慎。"
    if positive > negative:
        return "偏乐观", "成功获取的主要指数偏强，市场情绪偏乐观。"
    return "中性观望", "成功获取的指数方向不一致，适合继续观察."


def _default_category(category: str | None) -> str:
    return {"finance": "市场", "politics": "政策", "culture": "消费", "world_bank": "长期发展"}.get(category or "finance", "市场")


def _direction(votes: list[str]) -> str:
    if "偏谨慎" in votes:
        return "偏谨慎"
    if "偏利好" in votes:
        return "偏利好"
    return "不确定"


def _time_badge(article: NewsArticle | dict) -> str:
    return "年度" if _article_field(article, "category", "") == "world_bank" else "近期"
