from __future__ import annotations

import streamlit as st


def render_settings_panel(
    *,
    newsapi_key: str,
    serpapi_key: str,
    newsdata_key: str,
    reddit_configured: bool,
    x_configured: bool,
    instagram_configured: bool,
) -> None:
    if st.button("返回首页"):
        st.session_state["page"] = "Home"
        st.rerun()

    st.subheader("Settings")
    st.caption("API key 只从本地 .env 读取。这里仅显示状态，不显示密钥内容。")
    if st.button("手动刷新数据"):
        st.cache_data.clear()
        st.success("缓存已清除，返回页面后会重新获取数据。")

    st.markdown("#### 数据源")
    col1, col2 = st.columns(2)
    with col1:
        st.write("NewsAPI", "已配置" if newsapi_key else "未配置")
        st.write("SerpAPI Google News", "已配置" if serpapi_key else "未配置")
        st.write("NewsData.io", "已配置" if newsdata_key else "未配置")
        st.write("AKShare", "本地 Python 依赖")
    with col2:
        st.write("Reddit", "已配置" if reddit_configured else "未配置")
        st.write("X", "已配置" if x_configured else "未配置")
        st.write("Instagram", "已配置" if instagram_configured else "未配置")

    st.markdown("#### 运行偏好")
    st.session_state["allow_fallback"] = st.toggle("API 失败时使用本地兜底", value=st.session_state.get("allow_fallback", True))
    st.session_state["show_social_signals"] = st.toggle("显示社交媒体热点", value=st.session_state.get("show_social_signals", True))
    st.session_state["refresh_interval"] = st.slider("刷新间隔（分钟）", 5, 60, st.session_state.get("refresh_interval", 15))
    st.info("本应用用于财经信息学习和新闻分析辅助，不构成投资建议。")
