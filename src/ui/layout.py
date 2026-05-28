from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --paper:#f5f6f2; --surface:#fffefa; --surface-2:#f8faf6; --ink:#171914;
            --muted:#687066; --line:#d9ded1; --line-strong:#b9c1b1;
            --brass:#a2742a; --lake:#1f6f78; --moss:#5f7f45; --warn:#9b4d32;
            --shadow:0 18px 44px rgba(38,45,33,.08);
        }
        .stApp {
            background:
                linear-gradient(180deg, rgba(245,246,242,.96), rgba(252,252,248,.98) 38%, #fff 100%),
                repeating-linear-gradient(90deg, rgba(23,25,20,.025) 0, rgba(23,25,20,.025) 1px, transparent 1px, transparent 24px);
            color: var(--ink);
            padding-top: 0 !important;
        }
        section[data-testid="stSidebar"] {
            background: rgba(255,254,250,.96);
            border-right: 1px solid var(--line);
            box-shadow: 8px 0 28px rgba(38,45,33,.04);
        }
        .main .block-container { max-width: 1180px; padding-top: .35rem; padding-bottom: 4rem; }
        h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
        .top-banner-title {
            padding: 1.15rem 1.25rem .85rem;
            margin: .25rem 0 .55rem;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: linear-gradient(180deg, rgba(255,254,250,.98), rgba(248,250,246,.96));
            box-shadow: var(--shadow);
        }
        .app-title {
            font-family: "Songti SC", "STSong", Georgia, serif;
            font-size: clamp(1.9rem, 4vw, 2.75rem);
            line-height: 1.05;
            font-weight: 700;
            color: var(--ink);
        }
        .app-subtitle {
            margin-top: .35rem;
            color: var(--muted);
            font-size: .95rem;
        }
        .nav-divider {
            height: 2.1rem;
            width: 1px;
            margin: .15rem auto 0;
            background: var(--line-strong);
        }
        .settings-footer {
            margin-top: 2.25rem;
            padding-top: .75rem;
            border-top: 1px solid rgba(217,222,209,.72);
        }
        h1 {
            font-family: "Songti SC", "STSong", Georgia, serif;
            font-size: clamp(2.25rem, 5vw, 3.4rem);
            line-height: 1.04;
            font-weight: 700;
        }
        h4, [data-testid="stMarkdownContainer"] h4 {
            margin-top: 1.35rem;
            padding-top: .4rem;
            border-top: 1px solid rgba(217,222,209,.78);
            font-size: 1.04rem;
        }
        .news-card, .analysis-card, .ai-card {
            background: linear-gradient(180deg, rgba(255,254,250,.98), rgba(248,250,246,.96));
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: .86rem;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        .news-card:hover, .index-card:hover {
            border-color: var(--line-strong);
            transform: translateY(-1px);
            transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease;
            box-shadow: 0 22px 48px rgba(38,45,33,.11);
        }
        .news-card h3 { font-size: 1.02rem; line-height: 1.42; margin: 0 0 .58rem; }
        .news-flow-card p {
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .empty-state { border-style: dashed; background: rgba(248,250,246,.72); }
        .muted { color: var(--muted); font-size: .88rem; line-height: 1.5; }
        .pill {
            display:inline-flex; min-height:26px; align-items:center;
            padding:.18rem .55rem; border-radius:999px;
            background:#eef3e8; color:#445f31; border:1px solid #d6e0c9;
            font-size:.8rem; margin:.12rem .16rem .12rem 0;
        }
        .pill-blue { background:#e8f3f4; color:var(--lake); border-color:#c8dfe1; }
        .ai-card { padding: 0; border-color: #cfd7ca; }
        .ai-card-header {
            display:flex; align-items:center; justify-content:space-between; gap:.75rem;
            padding:.9rem 1rem; background:rgba(245,246,242,.72);
            border-bottom:1px solid var(--line);
        }
        .ai-kicker {
            font-size:.76rem; color:var(--brass); text-transform:uppercase;
            font-weight:700;
        }
        .ai-score {
            color:var(--muted); font-size:.82rem;
            border:1px solid var(--line); border-radius:999px; padding:.16rem .5rem;
            background:rgba(255,254,250,.78);
        }
        .ai-section {
            display:grid; grid-template-columns: 7.5rem 1fr; gap:.85rem;
            padding:.92rem 1rem; border-bottom:1px solid rgba(217,222,209,.68);
        }
        .ai-section:last-child { border-bottom: 0; }
        .ai-label { color:var(--lake); font-weight:700; font-size:.92rem; }
        .ai-copy { color:var(--ink); line-height:1.72; }
        .index-card p { font-family: Georgia, "Songti SC", serif; color:var(--ink); }
        div[data-testid="stButton"] button {
            border-radius: 0;
            border: 0 !important;
            background: transparent !important;
            color: var(--ink);
            box-shadow: none !important;
            min-height: 2.35rem;
            padding-left: .25rem;
            padding-right: .25rem;
        }
        div[data-testid="stButton"] button[kind="primary"] {
            border-radius: 999px !important;
            border: 1px solid var(--line-strong) !important;
            background: rgba(255,254,250,.86) !important;
            color: var(--ink) !important;
            box-shadow: none !important;
            padding-left: .85rem;
            padding-right: .85rem;
        }
        div[data-testid="stButton"] button:hover {
            border: 0 !important;
            background: transparent !important;
            color: var(--lake);
            box-shadow: none !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            border: 1px solid var(--lake) !important;
            background: rgba(232,243,244,.72) !important;
            color: var(--lake) !important;
            box-shadow: none !important;
        }
        div[data-testid="stButton"] button:focus {
            border: 0 !important;
            box-shadow: none !important;
            outline: none !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:focus {
            border: 1px solid var(--lake) !important;
            box-shadow: none !important;
            outline: none !important;
        }
        div[data-testid="stSelectbox"] > div, div[data-testid="stTextInput"] > div {
            border-radius: 8px;
        }
        div[data-testid="stMultiSelect"] > div {
            border-radius: 8px;
        }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
        [data-testid="stHeader"], .stDeployButton, #MainMenu, footer { display: none !important; visibility: hidden !important; }
        @media (max-width: 720px) {
            .main .block-container { padding-left: 1rem; padding-right: 1rem; }
            .ai-section { grid-template-columns: 1fr; gap:.28rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def banner(title: str, subtitle: str) -> bool:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    left, right = st.columns([7, 1.15])
    with left:
        st.markdown(f"<h1>{title}</h1><p>{subtitle}</p>", unsafe_allow_html=True)
    with right:
        st.write("")
        clicked = st.button("⋯", help="Settings")
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked
