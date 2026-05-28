from __future__ import annotations

import streamlit as st

from src.analysis.news_analyzer import AnalyzedNews
from src.ui.market_dashboard_page import render_analyzed_news_card


def render_news_center(analyzed_news: list[AnalyzedNews]) -> None:
    st.subheader("News Center / 新闻中心")
    if not analyzed_news:
        st.info("暂时没有新闻。")
        return
    sort_mode = st.selectbox("排序", ["影响评分最高", "原始顺序"])
    rows = analyzed_news
    if sort_mode == "影响评分最高":
        rows = sorted(rows, key=lambda item: item.impact_score, reverse=True)
    if not rows:
        st.info("当前筛选条件下暂无新闻。")
        return
    for item in rows:
        render_analyzed_news_card(item)
