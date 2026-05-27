from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from data_sources.akshare_provider import AK_SOURCE, fetch_akshare_snapshot, fetch_cn_index_spot, snapshot_from_dict, snapshot_to_dict
from data_sources.cache_store import load_or_refresh_json
from data_sources.tushare_provider import fetch_tushare_indices
from src.models import MarketIndex


CN_INDEX_TARGETS = [
    ("000001", "上证指数"),
    ("399001", "深证成指"),
    ("399006", "创业板指"),
    ("000300", "沪深300"),
    ("000905", "中证500"),
    ("000688", "科创50"),
]

GLOBAL_INDEX_TARGETS = [
    ("^HSI", "恒生指数", "HK"),
    ("HSTECH.HK", "恒生科技指数", "HK"),
    ("^GSPC", "标普500", "WEST"),
    ("^IXIC", "纳斯达克综合指数", "WEST"),
    ("^DJI", "道琼斯指数", "WEST"),
    ("^FTSE", "英国富时100", "WEST"),
    ("^GDAXI", "德国DAX", "WEST"),
    ("^FCHI", "法国CAC40", "WEST"),
]

AK_PROVIDER_TIMEOUT_SECONDS = 4
TUSHARE_PROVIDER_TIMEOUT_SECONDS = 4

FALLBACK_INDICES = [
    ("^GSPC", "S&P 500", "WEST"),
    ("^IXIC", "NASDAQ", "WEST"),
    ("^DJI", "Dow Jones", "WEST"),
    ("000300", "沪深300", "CN"),
    ("^HSI", "恒生指数", "HK"),
]


def get_market_response(data_dir: Path, ttl_seconds: int = 300) -> dict:
    cache_path = data_dir / "cache" / "market_cache.json"

    def loader() -> tuple[dict, str]:
        akshare_payload = _call_with_timeout(_load_akshare_market, AK_PROVIDER_TIMEOUT_SECONDS)
        if akshare_payload:
            return akshare_payload

        tushare_payload = _call_with_timeout(_load_tushare_market, TUSHARE_PROVIDER_TIMEOUT_SECONDS)
        if tushare_payload:
            return tushare_payload

        raise RuntimeError("market provider unavailable")

    payload = load_or_refresh_json(cache_path, ttl_seconds=ttl_seconds, loader=loader)
    data = payload.get("data") or {}
    payload["data"] = {
        "indices": [_index_from_dict(row) for row in data.get("indices", [])],
        "snapshot": snapshot_from_dict(data.get("snapshot", {})) if data.get("snapshot") else None,
    }
    if not payload["data"]["indices"]:
        payload["data"]["indices"] = fallback_indices()
        payload["source"] = "empty" if payload.get("source") == "empty" else payload.get("source", "empty")
        payload["status"] = "fallback"
        payload["message"] = "指数数据暂不可用，已展示 fallback 指数卡片。"
    print(f"[market-debug] response status={payload.get('status')} source={payload.get('source')} count={len(payload['data']['indices'])}")
    return payload


def _load_akshare_market() -> tuple[dict, str] | None:
    indices = fetch_market_indices()
    snapshot = fetch_akshare_snapshot(limit=8)
    has_snapshot = any([snapshot.a_spot_top, snapshot.index_spot, snapshot.concept_boards, snapshot.fund_flow])
    print(f"[market-debug] source=akshare status=loaded count={len(indices)} snapshot={int(has_snapshot)}")
    if any(index.status == "success" for index in indices) or has_snapshot:
        return {"indices": [_index_to_dict(index) for index in indices], "snapshot": snapshot_to_dict(snapshot)}, "akshare"
    return None


def _load_tushare_market() -> tuple[dict, str] | None:
    tushare_indices, status = fetch_tushare_indices()
    print(f"[market-debug] source=tushare status={status.get('status')} count={len(tushare_indices)} error={status.get('message', '')}")
    if tushare_indices:
        return {"indices": [_index_to_dict(index) for index in tushare_indices], "snapshot": None}, "tushare"
    return None


def _call_with_timeout(func, timeout_seconds: int) -> tuple[dict, str] | None:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func)
    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError:
        future.cancel()
        print(f"[market-debug] source={getattr(func, '__name__', 'provider')} status=timeout count=0 error=timeout")
        return None
    except Exception as exc:
        print(f"[market-debug] source={getattr(func, '__name__', 'provider')} status=error count=0 error={type(exc).__name__}")
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def fetch_market_indices() -> list[MarketIndex]:
    return load_cn_indices() + _load_global_indices()


def fallback_indices() -> list[MarketIndex]:
    return [
        MarketIndex(symbol, name, region, None, None, None, None, "fallback", datetime.now(), "fallback", "指数数据暂不可用")
        for symbol, name, region in FALLBACK_INDICES
    ]


def load_cn_indices() -> list[MarketIndex]:
    frame, status = fetch_cn_index_spot()
    if status.status == "error":
        return [_placeholder(symbol, name, "CN", "error", status.message, status.updated_at) for symbol, name in CN_INDEX_TARGETS]
    if frame.empty:
        return [_placeholder(symbol, name, "CN", "empty", "AKShare 暂无该指数数据。", status.updated_at) for symbol, name in CN_INDEX_TARGETS]
    indices: list[MarketIndex] = []
    for symbol, name in CN_INDEX_TARGETS:
        row = _match_index_row(frame, symbol, name)
        if row is None:
            indices.append(_placeholder(symbol, name, "CN", "empty", "AKShare 暂无该指数数据。", status.updated_at))
            continue
        indices.append(MarketIndex(str(row.get("代码") or symbol), name, "CN", _to_float(row.get("最新价")), _to_float(row.get("涨跌额")), _to_float(row.get("涨跌幅")), _to_float(row.get("成交额")), AK_SOURCE, status.updated_at or datetime.now(), "success", status.message))
    return indices


def fetch_index_history(symbol: str, period: str = "1mo") -> pd.DataFrame:
    if symbol.isdigit():
        return pd.DataFrame()
    try:
        import yfinance as yf
        history = yf.Ticker(symbol).history(period=period, interval="1d")
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame() if history.empty else history.reset_index()


def valid_sentiment_changes(indices: list[MarketIndex], max_age_minutes: int = 60 * 24) -> list[float | None]:
    now = datetime.now()
    return [index.change_pct for index in indices if index.status == "success" and index.change_pct is not None and index.updated_at is not None and now - index.updated_at <= timedelta(minutes=max_age_minutes)]


def _load_global_indices() -> list[MarketIndex]:
    try:
        import yfinance as yf
    except ImportError:
        return [_placeholder(symbol, name, region, "error", "缺少 yfinance。", None, "Yahoo Finance") for symbol, name, region in GLOBAL_INDEX_TARGETS]
    rows: list[MarketIndex] = []
    for symbol, name, region in GLOBAL_INDEX_TARGETS:
        try:
            rows.append(_index_from_history(name, region, symbol, yf.Ticker(symbol).history(period="5d", interval="1d")))
        except Exception as exc:
            rows.append(_placeholder(symbol, name, region, "error", type(exc).__name__, None, "Yahoo Finance"))
    return rows


def _index_from_history(name: str, region: str, symbol: str, history: pd.DataFrame) -> MarketIndex:
    if history.empty or "Close" not in history:
        return _placeholder(symbol, name, region, "empty", "暂无行情数据。", None, "Yahoo Finance")
    closes = history["Close"].dropna()
    if closes.empty:
        return _placeholder(symbol, name, region, "empty", "暂无行情数据。", None, "Yahoo Finance")
    latest = float(closes.iloc[-1])
    previous = float(closes.iloc[-2]) if len(closes) > 1 else latest
    change = latest - previous
    return MarketIndex(symbol, name, region, latest, change, (change / previous * 100) if previous else 0.0, None, "Yahoo Finance", datetime.now(), "success", "延迟 / 最近可用")


def _match_index_row(frame: pd.DataFrame, symbol: str, name: str) -> pd.Series | None:
    if "代码" in frame.columns:
        matched = frame[frame["代码"].astype(str).str.zfill(6) == symbol]
        if not matched.empty:
            return matched.iloc[0]
    if "名称" in frame.columns:
        matched = frame[frame["名称"].astype(str).str.contains(name, na=False, regex=False)]
        if not matched.empty:
            return matched.iloc[0]
    return None


def _placeholder(symbol: str, name: str, region: str, status: str, message: str, updated_at: datetime | None, source: str = AK_SOURCE) -> MarketIndex:
    return MarketIndex(symbol, name, region, None, None, None, None, source, updated_at, status, message)


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _index_to_dict(index: MarketIndex) -> dict:
    return {"symbol": index.symbol, "name": index.name, "region": index.region, "price": index.price, "change": index.change, "change_pct": index.change_pct, "turnover": index.turnover, "source": index.source, "updated_at": index.updated_at.isoformat() if index.updated_at else None, "status": index.status, "message": index.message}


def _index_from_dict(row: dict) -> MarketIndex:
    updated_at = None
    if row.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(row["updated_at"])
        except ValueError:
            updated_at = None
    return MarketIndex(str(row.get("symbol", "")), str(row.get("name", "")), str(row.get("region", "")), _to_float(row.get("price")), _to_float(row.get("change")), _to_float(row.get("change_pct")), _to_float(row.get("turnover")), str(row.get("source", "")), updated_at, str(row.get("status", "empty")), str(row.get("message", "")))
