from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import APP_SUBTITLE, APP_TITLE, CONFIG_DIR, DATA_DIR, DEFAULT_NEWS_LIMIT
from src.api_config import env_list, env_value, load_local_env
from src.analysis.news_analyzer import preview_news_items
from data_sources.announcement_provider import get_announcements_response
from data_sources.market_service import get_market_response
from data_sources.report_provider import get_reports_response
from src.news_filters import NewsFilterRequest, filter_analyzed_news, filter_grouped_news
from src.news_fetcher import NewsFetcher
from data_sources.news_service import get_news_response
from src.rss_sources import load_sources
from src.social.aggregator import collect_trends
from src.social.instagram_client import InstagramClient
from src.social.reddit_client import RedditClient
from src.social.x_client import XClient
from src.ui.index_detail_page import render_index_detail
from src.ui.layout import apply_theme
from src.ui.market_dashboard_page import render_market_dashboard
from src.ui.news_center_page import render_news_center
from src.ui.settings_panel import render_settings_panel
from src.world_bank_client import WorldBankDocumentsClient
from src.world_bank_indicators import WorldBankIndicatorsClient


HOME_NEWS_LIMIT = 20


load_local_env(ROOT)
st.set_page_config(
    page_title="News For Me",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)
apply_theme()

@st.cache_data(ttl=900)
def get_sources() -> dict:
    return load_sources(CONFIG_DIR / "sources.yaml")


@st.cache_data(ttl=900)
def get_news(newsapi_key: str, serpapi_key: str, newsdata_key: str, allow_fallback: bool, limit: int) -> dict:
    return get_news_response(
        fetcher=NewsFetcher(),
        sources=get_sources(),
        data_dir=DATA_DIR,
        newsapi_key=newsapi_key,
        serpapi_key=serpapi_key,
        newsdata_key=newsdata_key,
        limit=limit,
    )


@st.cache_data(ttl=900)
def get_trends(
    reddit_client_id: str,
    reddit_client_secret: str,
    reddit_user_agent: str,
    reddit_subreddits: tuple[str, ...],
    x_bearer_token: str,
    x_queries: tuple[str, ...],
    instagram_access_token: str,
    instagram_ig_user_id: str,
    instagram_hashtags: tuple[str, ...],
    graph_version: str,
    limit: int,
):
    clients = [
        RedditClient(reddit_client_id, reddit_client_secret, reddit_user_agent, list(reddit_subreddits)),
        XClient(x_bearer_token, list(x_queries)),
        InstagramClient(instagram_access_token, instagram_ig_user_id, list(instagram_hashtags), graph_version),
    ]
    return collect_trends(clients, limit=limit)


@st.cache_data(ttl=86400)
def get_world_bank_documents(query: str, limit: int):
    return WorldBankDocumentsClient().fetch_latest(limit=limit, query=query)


@st.cache_data(ttl=86400)
def get_world_bank_indicators(country: str):
    return WorldBankIndicatorsClient().fetch_indicators(country=country)


@st.cache_data(ttl=300)
def get_market_payload():
    return get_market_response(DATA_DIR)


def filter_news(grouped_news: dict, keyword: str) -> dict:
    return filter_grouped_news(grouped_news, keyword)


def flatten_news(grouped_news: dict, extra_articles: list) -> list:
    articles = []
    for category in ["finance", "politics", "culture"]:
        articles.extend(grouped_news.get(category, []))
    articles.extend(extra_articles)
    return articles


def load_news_context(
    *,
    keyword: str,
    limit: int,
    include_world_bank: bool,
    newsapi_key: str,
    serpapi_key: str,
    newsdata_key: str,
    allow_fallback: bool,
):
    news_payload = get_news(newsapi_key, serpapi_key, newsdata_key, allow_fallback, limit)
    grouped = filter_news(news_payload["data"], keyword)
    documents = get_world_bank_documents(keyword or "economic update", 5) if include_world_bank else []
    analyzed = preview_news_items(flatten_news(grouped, documents))
    return grouped, documents, analyzed, news_payload


def render_link_entries(title: str, rows: list[dict]) -> None:
    st.subheader(title)
    for row in rows:
        st.markdown(
            f"""
            <div class="news-card link-card">
                <div class="muted">{escape(str(row.get("source", "")))} · {escape(str(row.get("type", title)))}</div>
                <h3>{escape(str(row.get("name", "")))}</h3>
                <a href="{escape(str(row.get("url", "")))}" target="_blank">打开链接</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_top_banner() -> None:
    nav_cols = st.columns([3.8, .82, 0.06, 1.05, 0.06, .82, 0.06, .82])
    with nav_cols[0]:
        st.write("")
    with nav_cols[1]:
        if st.button("首页", use_container_width=True):
            st.session_state["page"] = "Home"
    with nav_cols[2]:
        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    with nav_cols[3]:
        if st.button("研报中心", use_container_width=True):
            st.session_state["page"] = "Reports"
    with nav_cols[4]:
        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    with nav_cols[5]:
        if st.button("年报", use_container_width=True):
            st.session_state["page"] = "Annual Reports"
    with nav_cols[6]:
        st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    with nav_cols[7]:
        if st.button("公告", use_container_width=True):
            st.session_state["page"] = "Announcements"
    action_cols = st.columns([1.25, 1.05, 5.7])
    with action_cols[0]:
        if st.button("加载指数和市场行情", use_container_width=True, type="primary"):
            st.session_state["load_market_data"] = True
            st.rerun()
    with action_cols[1]:
        if st.button("刷新数据", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    with action_cols[2]:
        st.write("")
    st.markdown(
        """
        <div class="top-banner-title">
            <div class="app-title">News For Me</div>
            <div class="app-subtitle">个人财经信息工作台</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_entry_cards(title: str, rows: list[dict]) -> None:
    st.markdown(f"### {title}")
    for row in rows:
        name = escape(str(row.get("name", row.get("source", ""))))
        row_type = escape(str(row.get("type", title)))
        description = escape(str(row.get("description", "")))
        url = escape(str(row.get("url", "")))
        st.markdown(
            f"""
            <div class="news-card link-card">
                <div class="muted">{row_type}</div>
                <h3>{name}</h3>
                <p>{description}</p>
                <a href="{url}" target="_blank">打开链接</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_reports_page() -> None:
    rows = get_reports_response().get("data", [])
    render_entry_cards("研报中心", rows)


def render_annual_reports_page() -> None:
    rows = [
        {
            "name": "巨潮资讯",
            "type": "年报 / 季报 / 公告",
            "description": "A股上市公司法定信息披露入口。",
            "url": "https://www.cninfo.com.cn/",
        },
        {
            "name": "上交所公告",
            "type": "沪市公告",
            "description": "查询沪市上市公司公告、年报和临时披露。",
            "url": "https://www.sse.com.cn/disclosure/listedinfo/announcement/",
        },
        {
            "name": "深交所公告",
            "type": "深市公告",
            "description": "查询深市上市公司公告、年报和临时披露。",
            "url": "https://www.szse.cn/disclosure/listed/notice/index.html",
        },
    ]
    render_entry_cards("年报", rows)


def calculate_importance_score(item) -> int:
    title = str(getattr(item, "title", "") or "")
    content = str(getattr(item, "content", "") or getattr(item, "summary", "") or "")
    source = str(getattr(item, "source", "") or "")
    text = f"{title} {content} {source}"
    score = 0
    source_weights = {
        "巨潮资讯": 5,
        "上交所": 5,
        "深交所": 5,
        "东方财富": 4,
        "财联社": 4,
        "证券时报": 4,
        "中国证券报": 4,
    }
    for key, weight in source_weights.items():
        if key in source:
            score += weight
    high_impact_keywords = ["年报", "季报", "业绩", "并购", "重组", "减持", "增持", "监管", "问询", "处罚", "降息", "加息", "财政", "货币政策", "出口", "房地产", "AI", "半导体", "新能源", "银行", "券商"]
    for keyword in high_impact_keywords:
        if keyword in text:
            score += 2
    if "公告" in text or "研报" in text:
        score += 3
    return score


def get_tag_options() -> list[str]:
    return [
        "AI",
        "半导体",
        "新能源",
        "房地产",
        "银行",
        "券商",
        "消费",
        "出口",
        "财政",
        "货币政策",
        "年报",
        "季报",
        "业绩",
        "并购",
        "重组",
        "监管",
        "问询",
        "处罚",
    ]


def filter_by_selected_tags(items: list, selected_tags: list[str]) -> list:
    if not selected_tags:
        return items
    lowered_tags = [tag.lower() for tag in selected_tags]
    filtered = []
    for item in items:
        fields = [
            str(getattr(item, "title", "") or ""),
            str(getattr(item, "content", "") or getattr(item, "summary", "") or ""),
            str(getattr(item, "source", "") or ""),
        ]
        item_tags = getattr(item, "tags", []) or []
        text = " ".join(fields + [str(tag) for tag in item_tags]).lower()
        if any(tag in text for tag in lowered_tags):
            filtered.append(item)
    return filtered



st.session_state.setdefault("page", "Home")
render_top_banner()
page = st.session_state.get("page", "Home")

selected_tags = st.multiselect("标签筛选", get_tag_options(), placeholder="选择主题标签")
keyword = ""
sort_mode = st.selectbox("排序方式", ["重要性优先", "最新优先"], index=0)
category_filter = "全部"
sentiment_filter = "全部"
time_filter = "近 3 天"
limit = max(DEFAULT_NEWS_LIMIT, HOME_NEWS_LIMIT)
load_market_data = st.session_state.get("load_market_data", False)
newsapi_key = env_value("NEWSAPI_KEY") or env_value("NEWS_API_KEY")
serpapi_key = env_value("SERPAPI_API_KEY")
newsdata_key = env_value("NEWSDATA_API_KEY")
reddit_client_id = env_value("REDDIT_CLIENT_ID")
reddit_client_secret = env_value("REDDIT_CLIENT_SECRET")
reddit_user_agent = env_value("REDDIT_USER_AGENT", "news_forme_local/0.1")
reddit_subreddits = tuple(env_list("REDDIT_SUBREDDITS", "China_irl,investing,Economics,worldnews"))
x_bearer_token = env_value("X_BEARER_TOKEN")
x_queries = tuple(env_list("X_QUERIES", "中国市场 OR A股,人民币 汇率,半导体 OR AI芯片"))
instagram_access_token = env_value("INSTAGRAM_ACCESS_TOKEN")
instagram_ig_user_id = env_value("INSTAGRAM_IG_USER_ID")
instagram_hashtags = tuple(env_list("INSTAGRAM_HASHTAGS", "财经,A股,半导体,文旅"))
graph_version = env_value("META_GRAPH_VERSION", "v25.0")
allow_fallback = st.session_state.get("allow_fallback", True)

context_args = {
    "keyword": keyword.strip(),
    "limit": limit,
    "newsapi_key": newsapi_key,
    "serpapi_key": serpapi_key,
    "newsdata_key": newsdata_key,
    "allow_fallback": allow_fallback,
}
filter_request = NewsFilterRequest(category_filter, keyword.strip(), sentiment_filter, time_filter)


if page == "Settings":
    render_settings_panel(
        newsapi_key=newsapi_key,
        serpapi_key=serpapi_key,
        newsdata_key=newsdata_key,
        reddit_configured=bool(reddit_client_id and reddit_client_secret),
        x_configured=bool(x_bearer_token),
        instagram_configured=bool(instagram_access_token and instagram_ig_user_id),
    )
elif page == "Home":
    _, world_bank_documents, analyzed_news, news_payload = load_news_context(include_world_bank=False, **context_args)
    analyzed_news = filter_analyzed_news(analyzed_news, filter_request)
    analyzed_news = filter_by_selected_tags(analyzed_news, selected_tags)
    if sort_mode == "重要性优先":
        analyzed_news = sorted(analyzed_news, key=calculate_importance_score, reverse=True)
    market_payload = get_market_payload()
    render_market_dashboard(
        market_payload["data"]["indices"],
        analyzed_news,
        world_bank_documents,
        get_world_bank_indicators("CHN"),
        market_payload["data"]["snapshot"],
        [],
        False,
        market_payload=market_payload,
        akshare_payload=market_payload,
    )
elif page == "Market Dashboard":
    _, world_bank_documents, analyzed_news, news_payload = load_news_context(include_world_bank=False, **context_args)
    analyzed_news = filter_analyzed_news(analyzed_news, filter_request)
    analyzed_news = filter_by_selected_tags(analyzed_news, selected_tags)
    trends = (
        get_trends(
            reddit_client_id,
            reddit_client_secret,
            reddit_user_agent,
            reddit_subreddits,
            x_bearer_token,
            x_queries,
            instagram_access_token,
            instagram_ig_user_id,
            instagram_hashtags,
            graph_version,
            10,
        )
        if st.session_state.get("show_social_signals", True)
        else []
    )
    market_payload = get_market_payload()
    market_indices = market_payload["data"]["indices"]
    akshare_snapshot = market_payload["data"]["snapshot"]
    render_market_dashboard(
        market_indices,
        analyzed_news,
        world_bank_documents,
        get_world_bank_indicators("CHN"),
        akshare_snapshot,
        trends,
        st.session_state.get("show_social_signals", True),
        market_payload=market_payload,
        akshare_payload=market_payload,
    )
elif page == "News Center":
    _, _, analyzed_news, news_payload = load_news_context(include_world_bank=False, **context_args)
    analyzed_news = filter_analyzed_news(analyzed_news, filter_request)
    analyzed_news = filter_by_selected_tags(analyzed_news, selected_tags)
    if sort_mode == "重要性优先":
        analyzed_news = sorted(analyzed_news, key=calculate_importance_score, reverse=True)
    render_news_center(analyzed_news)
elif page == "Index Detail":
    _, _, analyzed_news, _ = load_news_context(include_world_bank=False, **context_args)
    analyzed_news = filter_analyzed_news(analyzed_news, filter_request)
    analyzed_news = filter_by_selected_tags(analyzed_news, selected_tags)
    market_indices = get_market_payload()["data"]["indices"]
    render_index_detail(market_indices, filter_analyzed_news(analyzed_news, filter_request))
elif page == "Reports":
    render_reports_page()
elif page == "Annual Reports":
    render_annual_reports_page()
elif page == "Announcements":
    render_entry_cards("公告", get_announcements_response()["data"])
st.markdown('<div class="settings-footer">', unsafe_allow_html=True)
footer_cols = st.columns([1, 6])
with footer_cols[0]:
    if st.button("Settings", key="footer_settings_button"):
        st.session_state["page"] = "Settings"
        st.rerun()
with footer_cols[1]:
    st.write("")
st.markdown('</div>', unsafe_allow_html=True)
