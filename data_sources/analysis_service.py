from __future__ import annotations

from data_sources.cache_store import response
from src.analysis.news_analyzer import analyze_news_item
from src.models import NewsArticle


def analyze_response(article: NewsArticle) -> dict:
    analysis = analyze_news_item(article)
    return response(
        "success",
        "sample",
        {
            "summary": analysis.ai_analysis["事实摘要"],
            "targets": analysis.impact_targets,
            "sentiment": analysis.impact_direction,
            "score": analysis.impact_score,
            "explanation": analysis.ai_analysis["经济学机制"],
            "risk": analysis.ai_analysis["不确定性"],
            "analysis": analysis,
        },
        "已生成本地规则解读。",
    )
