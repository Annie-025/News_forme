from __future__ import annotations

from html import escape

import streamlit as st

from src.models import MarketIndex, NewsArticle, SocialTrend, article_field


def pills(items: list[str], blue: bool = False) -> str:
    style = "pill pill-blue" if blue else "pill"
    return " ".join(f'<span class="{style}">{escape(item)}</span>' for item in items) or '<span class="muted">暂无</span>'


def news_card(article: NewsArticle, summary: str = "") -> None:
    article_link = article_field(article, "link") or article_field(article, "url")
    link = f'<a href="{escape(article_link)}" target="_blank">原文链接</a>' if article_link else ""
    st.markdown(
        f"""
        <div class="news-card">
            <div class="muted">{escape(article_field(article, "source"))} · {escape(article_field(article, "date"))}</div>
            <h3>{escape(article_field(article, "title"))}</h3>
            <p>{escape(summary or article_field(article, "content"))}</p>
            {link}
        </div>
        """,
        unsafe_allow_html=True,
    )


def trend_card(trend: SocialTrend) -> None:
    st.markdown(
        f"""
        <div class="news-card">
            <div class="muted">{escape(trend.platform)} · 热度 {trend.heat}</div>
            <h3>{escape(trend.topic)}</h3>
            <p>{escape(trend.summary)}</p>
            <p>{pills(trend.keywords)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def market_index_card(index: MarketIndex | dict) -> None:
    name = _index_field(index, "name", "symbol", default="未知指数")
    region = _index_field(index, "region", default="")
    source = _index_field(index, "source", default="")
    status = _index_field(index, "status", default="empty")
    price = _index_field(index, "value", "price", "close", default=None)
    change_pct = _index_field(index, "change_pct", "pct_change", "percent", default=None)
    updated = _index_field(index, "updated_at_text", "updated_at", default="暂无")
    if status == "success":
        value = f"{float(price):,.2f}" if price is not None else "暂不可用"
        change = f"{float(change_pct):+.2f}%" if change_pct is not None else "暂不可用"
    else:
        value = "暂无数据 / 暂不可用"
        change = "等待可用行情"
        updated = "暂无"
    direction_class = "pill" if (change_pct or 0) >= 0 and status == "success" else "pill pill-blue"
    st.markdown(
        f"""
        <div class="news-card index-card">
            <div class="muted">{escape(str(region))} · {escape(str(source))}</div>
            <h3>{escape(str(name))}</h3>
            <p style="font-size:1.35rem;font-weight:700;margin:.3rem 0;">{escape(value)}</p>
            <span class="{direction_class}">{escape(change)}</span>
            <div class="muted" style="margin-top:.55rem;">更新：{escape(str(updated))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _index_field(index: MarketIndex | dict, *names: str, default=""):
    for name in names:
        if isinstance(index, dict):
            value = index.get(name)
        else:
            value = getattr(index, name, None)
            if value is None and name == "updated_at_text":
                value = getattr(index, "updated_at_text", None)
        if value is not None:
            return value
    return default
