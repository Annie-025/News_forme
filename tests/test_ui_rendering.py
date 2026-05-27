from __future__ import annotations

from src.analysis.news_analyzer import AnalyzedNews
from src.models import NewsArticle


def _analysis_item() -> AnalyzedNews:
    return AnalyzedNews(
        article=NewsArticle("测试新闻", "测试内容", "测试源", "2026-05-26", "", "finance"),
        content_category="市场",
        display_tags=["市场", "不确定", "近期"],
        impact_targets=["A股"],
        impact_direction="不确定",
        impact_score=42,
        ai_analysis={
            "事实摘要": "宏观数据继续影响风险偏好。",
            "经济学机制": "资金流和政策预期共同作用。",
            "可能影响": "短期市场可能维持震荡。",
            "不确定性": "需要观察成交量和政策落地。",
        },
    )


def test_ai_analysis_renders_as_single_complete_card(monkeypatch):
    import src.ui.market_dashboard_page as page

    rendered: list[str] = []
    monkeypatch.setattr(page.st, "markdown", lambda body, **kwargs: rendered.append(body))

    page.render_ai_analysis(_analysis_item())

    assert len(rendered) == 1
    html = rendered[0]
    assert 'class="ai-card"' in html
    assert html.count('class="ai-section"') == 4
    assert html.count("<div") == html.count("</div>")
    assert "事实摘要" in html
    assert "不确定性" in html
