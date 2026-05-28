from __future__ import annotations

import sys
import types

import pandas as pd

from src.models import SourceStatus


def test_safe_ak_call_returns_error_when_akshare_missing(monkeypatch):
    import src.akshare_data as akshare_data

    monkeypatch.setitem(sys.modules, "akshare", None)

    df, status = akshare_data.safe_ak_call("stock_zh_index_spot_em", symbol="沪深重要指数")

    assert df.empty
    assert status.status == "error"
    assert "未安装" in status.message


def test_load_cn_indices_handles_empty_dataframe(monkeypatch):
    import data_sources.market_service as market_data

    monkeypatch.setattr(
        market_data,
        "fetch_cn_index_spot",
        lambda: (pd.DataFrame(), SourceStatus("AKShare CN indices", True, "empty", "empty", None)),
    )

    indices = market_data.load_cn_indices()

    assert len(indices) == len(market_data.CN_INDEX_TARGETS)
    assert {index.status for index in indices} == {"empty"}


def test_load_cn_indices_converts_dataframe(monkeypatch):
    import data_sources.market_service as market_data

    frame = pd.DataFrame(
        [
            {"代码": "000001", "名称": "上证指数", "最新价": 3100.5, "涨跌额": 12.3, "涨跌幅": 0.4, "成交额": 1000},
            {"代码": "399001", "名称": "深证成指", "最新价": 9800.0, "涨跌额": -21.0, "涨跌幅": -0.21, "成交额": 2000},
            {"代码": "399006", "名称": "创业板指", "最新价": 1900.0, "涨跌额": 10.0, "涨跌幅": 0.53, "成交额": 900},
            {"代码": "000300", "名称": "沪深300", "最新价": 3600.0, "涨跌额": 5.0, "涨跌幅": 0.14, "成交额": 800},
            {"代码": "000905", "名称": "中证500", "最新价": 5400.0, "涨跌额": 7.0, "涨跌幅": 0.13, "成交额": 700},
            {"代码": "000688", "名称": "科创50", "最新价": 820.0, "涨跌额": 3.0, "涨跌幅": 0.37, "成交额": 600},
        ]
    )
    monkeypatch.setattr(
        market_data,
        "fetch_cn_index_spot",
        lambda: (frame, SourceStatus("AKShare CN indices", True, "success", "ok", None)),
    )

    indices = market_data.load_cn_indices()

    sh = next(index for index in indices if index.name == "上证指数")
    assert sh.symbol == "000001"
    assert sh.region == "CN"
    assert sh.price == 3100.5
    assert sh.change_pct == 0.4
    assert sh.status == "success"
    assert sh.source == "AKShare / 东方财富"


def test_load_cn_indices_keeps_other_indices_when_one_missing(monkeypatch):
    import data_sources.market_service as market_data

    frame = pd.DataFrame(
        [{"代码": "000001", "名称": "上证指数", "最新价": 3100.5, "涨跌额": 12.3, "涨跌幅": 0.4, "成交额": 1000}]
    )
    monkeypatch.setattr(
        market_data,
        "fetch_cn_index_spot",
        lambda: (frame, SourceStatus("AKShare CN indices", True, "success", "ok", None)),
    )

    indices = market_data.load_cn_indices()

    assert next(index for index in indices if index.name == "上证指数").status == "success"
    assert next(index for index in indices if index.name == "深证成指").status == "empty"


def test_fetch_market_indices_keeps_cn_indices_when_global_provider_fails(monkeypatch):
    import data_sources.market_service as market_data
    from src.models import MarketIndex

    cn_index = MarketIndex(
        symbol="000001",
        name="上证指数",
        region="CN",
        price=3100.5,
        change=12.3,
        change_pct=0.4,
        turnover=1000,
        source="AKShare / 东方财富",
        updated_at=None,
        status="success",
    )
    monkeypatch.setattr(market_data, "load_cn_indices", lambda: [cn_index])
    monkeypatch.setattr(market_data, "_load_global_indices", lambda: (_ for _ in ()).throw(RuntimeError("global timeout")))

    indices = market_data.fetch_market_indices()

    assert indices == [cn_index]


def test_source_status_sanitizes_sensitive_values():
    status = SourceStatus(
        name="AKShare",
        configured=True,
        status="error",
        message="failed with token=abc123 and api_key=secret&client_secret=hidden",
        updated_at=None,
    )

    assert "abc123" not in status.message
    assert "secret" not in status.message
    assert "hidden" not in status.message


def test_global_indices_include_hk_and_western_markets():
    import data_sources.market_service as market_data

    regions = {region for _, _, region in market_data.GLOBAL_INDEX_TARGETS}
    names = {name for _, name, _ in market_data.GLOBAL_INDEX_TARGETS}

    assert "HK" in regions
    assert "WEST" in regions
    assert {"恒生指数", "标普500", "德国DAX"}.issubset(names)


def test_market_index_card_hides_loading_status_text(monkeypatch):
    from datetime import datetime

    import src.ui.components as components
    from src.models import MarketIndex

    rendered: list[str] = []
    monkeypatch.setattr(components.st, "markdown", lambda body, **kwargs: rendered.append(body))

    components.market_index_card(
        MarketIndex(
            symbol="000001",
            name="上证指数",
            region="CN",
            price=None,
            change=None,
            change_pct=None,
            turnover=None,
            source="AKShare / 东方财富",
            updated_at=datetime(2026, 5, 25, 9, 30),
            status="error",
            message="ProxyError: 127.0.0.1:7890 unavailable",
        )
    )

    html = "\n".join(rendered)
    assert "请求失败" not in html
    assert "成功" not in html
    assert "ProxyError" not in html
    assert "暂无数据" in html
