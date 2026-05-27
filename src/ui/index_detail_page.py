from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analysis.news_analyzer import AnalyzedNews
from data_sources.market_service import fetch_index_history
from src.models import MarketIndex
from src.ui.components import market_index_card
from src.ui.market_dashboard_page import render_analyzed_news_card


def render_index_detail(indices: list[MarketIndex], analyzed_news: list[AnalyzedNews]) -> None:
    st.subheader("Index Detail / 指数详情")
    if not indices:
        st.info("暂时没有指数数据。")
        return
    selected_name = st.selectbox("选择指数", [index.name for index in indices])
    selected = next(index for index in indices if index.name == selected_name)
    market_index_card(selected)
    if selected.region != "CN" and selected.status == "success":
        history = fetch_index_history(selected.symbol)
        if not history.empty and "Close" in history:
            st.plotly_chart(px.line(history, x=history.columns[0], y="Close", title=f"{selected.name} 最近走势"), use_container_width=True)
        else:
            st.info("最近走势暂不可用。")

    related = _related_news(selected, analyzed_news)
    st.markdown("#### 影响该指数的相关新闻")
    if not related:
        st.info("暂时没有与该指数明显相关的高影响新闻。")
        return
    for item in related[:5]:
        render_analyzed_news_card(item)


def _related_news(index: MarketIndex, analyzed_news: list[AnalyzedNews]) -> list[AnalyzedNews]:
    keywords_by_region = {
        "CN": ["A股", "人民币", "消费", "创业板", "整体市场"],
        "HK": ["港股", "人民币", "整体市场"],
        "WEST": ["美股", "欧美", "科技", "整体市场"],
    }
    keywords = keywords_by_region.get(index.region, ["整体市场"])
    return [item for item in analyzed_news if any(keyword in target for keyword in keywords for target in item.impact_targets)]
