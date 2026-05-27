from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from data_sources.analysis_service import analyze_response
from src.analysis.news_analyzer import AnalyzedNews, market_sentiment
from data_sources.market_service import valid_sentiment_changes
from src.models import AkShareSnapshot, MarketIndex, NewsArticle, SocialTrend, article_field
from src.ui.components import market_index_card, news_card, pills, trend_card
from src.world_bank_indicators import WorldBankIndicator, dashboard_eligible_indicators


def render_market_dashboard(
    indices: list[MarketIndex],
    analyzed_news: list[AnalyzedNews],
    world_bank_documents: list[NewsArticle],
    world_bank_indicators: list[WorldBankIndicator],
    akshare_snapshot: AkShareSnapshot | None,
    trends: list[SocialTrend],
    show_social_signals: bool,
    market_payload: dict | None = None,
    akshare_payload: dict | None = None,
) -> None:
    st.markdown("#### 主要指数")
    if indices:
        render_data_status("市场指数", market_payload or {})
        for region, label in [("CN", "中国大陆"), ("HK", "香港市场"), ("WEST", "欧美市场")]:
            region_indices = [index for index in indices if index.region == region]
            if not region_indices:
                continue
            st.markdown(f"**{label}**")
            cols = st.columns(min(3, len(region_indices)) or 1)
            for col, index in zip(cols, region_indices):
                with col:
                    market_index_card(index)

    sentiment, explanation = market_sentiment(valid_sentiment_changes(indices), analyzed_news)
    st.markdown("#### 今日市场情绪")
    st.markdown(
        f"""
        <div class="analysis-card">
            <p><b>情绪判断：</b>{escape(sentiment)}</p>
            <p>{escape(explanation)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if akshare_snapshot is not None:
        render_data_status("A 股快照", akshare_payload or {})
        render_akshare_snapshot(akshare_snapshot)

    st.markdown("#### 重点新闻")
    if not analyzed_news:
        render_empty_state("当前筛选条件下暂无新闻。")
    for item in analyzed_news[:8]:
        render_analyzed_news_card(item)

    if show_social_signals and trends:
        st.markdown("#### 热点信号")
        for trend in trends[:2]:
            trend_card(trend)


def render_akshare_snapshot(snapshot: AkShareSnapshot) -> None:
    st.markdown("#### A 股市场快照")
    st.caption(f"AKShare 数据抓取时间：{snapshot.updated_at_text}")

    col1, col2, col3 = st.columns(3)
    with col1:
        render_activity_chart(snapshot.market_activity)
    with col2:
        render_bar_chart("概念热度", snapshot.concept_boards, "板块名称", "涨跌幅")
    with col3:
        render_bar_chart("资金流向", snapshot.fund_flow, "名称", "今日主力净流入-净额")

def render_activity_chart(rows: list[dict]) -> None:
    st.markdown("**市场活跃度**")
    df = _rows_to_dataframe(rows, "item", "value")
    if df.empty:
        st.caption("暂无数据")
        return
    st.plotly_chart(px.line(df, x="name", y="value", markers=True), use_container_width=True)


def render_bar_chart(title: str, rows: list[dict], name_col: str, value_col: str) -> None:
    st.markdown(f"**{title}**")
    df = _rows_to_dataframe(rows, name_col, value_col)
    if df.empty:
        st.caption("暂无数据")
        return
    st.plotly_chart(px.bar(df, x="name", y="value", text="value"), use_container_width=True)


def render_compact_rows(title: str, rows: list[dict], columns: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not rows:
        st.caption("暂无数据")
        return
    for row in rows[:8]:
        st.caption(" · ".join(f"{column}: {row.get(column, '')}" for column in columns if row.get(column, "") != ""))


def render_analyzed_news_card(item: AnalyzedNews) -> None:
    article = item.article
    title = article_field(article, "title")
    source = article_field(article, "source")
    date = article_field(article, "date")
    st.markdown(
        f"""
        <div class="news-card news-flow-card">
            <div class="muted">{escape(source)} · {escape(date)}</div>
            <h3>{escape(title)}</h3>
            <p><b>摘要：</b>{escape(item.ai_analysis.get("事实摘要", title))}</p>
            <p>{pills(item.display_tags, blue=True)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    key = f"ai_{abs(hash(title + source))}"
    if st.button("AI 解读", key=key, help="展开这条新闻的规则分析"):
        st.session_state[key + "_open"] = not st.session_state.get(key + "_open", False)
    if st.session_state.get(key + "_open", False):
        payload = analyze_response(article)
        if payload["status"] == "success":
            render_ai_analysis(payload["data"]["analysis"])
        else:
            st.info("AI 解读暂时不可用，请稍后再试。")


def render_ai_analysis(item: AnalyzedNews) -> None:
    sections = "".join(
        f"""
        <div class="ai-section">
            <div class="ai-label">{escape(label)}</div>
            <div class="ai-copy">{escape(item.ai_analysis[label])}</div>
        </div>
        """
        for label in ["事实摘要", "经济学机制", "可能影响", "不确定性"]
    )
    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-card-header">
                <div>
                    <div class="ai-kicker">Rule-based brief</div>
                    <strong>{escape(item.content_category)} · {escape(item.impact_direction)}</strong>
                </div>
                <span class="ai-score">影响评分 {item.impact_score}</span>
            </div>
            {sections}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_world_bank_indicators(indicators: list[WorldBankIndicator]) -> None:
    st.markdown("#### World Bank 长期指标")
    visible = dashboard_eligible_indicators(indicators)
    if not visible:
        st.caption("暂无足够新的 World Bank 指标。")
        return
    for indicator in visible:
        st.write(indicator.indicator_name, indicator.latest_value)


def render_data_status(label: str, payload: dict) -> None:
    status = payload.get("status", "idle")
    source = payload.get("source", "")
    badge = {"success": "实时", "fallback": "缓存", "error": "暂不可用", "idle": "待加载"}.get(status, status)
    st.caption(f"{label} · {badge} · {source}")


def render_empty_state(message: str) -> None:
    st.markdown(
        f"""
        <div class="analysis-card empty-state">
            <b>暂无匹配内容</b>
            <p class="muted">{escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _rows_to_dataframe(rows: list[dict], name_col: str, value_col: str) -> pd.DataFrame:
    records = []
    for row in rows:
        value = _to_number(row.get(value_col))
        name = row.get(name_col)
        if name is not None and value is not None:
            records.append({"name": str(name), "value": value})
    return pd.DataFrame(records)


def _to_number(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("%", "").strip())
        except ValueError:
            return None
    return None
