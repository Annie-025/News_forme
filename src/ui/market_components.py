from __future__ import annotations

import streamlit as st


def render_market_loading_status(payload: dict | None) -> None:
    if not payload:
        return
    status = str(payload.get("status", "idle"))
    source = str(payload.get("source", ""))
    message = str(payload.get("message", "")).strip()
    label = {
        "success": "已更新",
        "fallback": "使用缓存",
        "error": "暂不可用",
        "idle": "待加载",
    }.get(status, status)
    detail = message or ("使用本地缓存。" if source == "cache" else "")
    st.caption(f"指数：{label}{f' · {detail}' if detail else ''}")
