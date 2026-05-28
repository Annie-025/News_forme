from __future__ import annotations

from datetime import datetime

from src.models import MarketIndex, sanitize_message


TUSHARE_SOURCE = "tushare"
TUSHARE_INDEX_TARGETS = [
    ("sh", "上证指数", "CN"),
    ("sz", "深证成指", "CN"),
    ("cyb", "创业板指", "CN"),
    ("hs300", "沪深300", "CN"),
    ("sz50", "上证50", "CN"),
    ("zxb", "中小板指", "CN"),
]


def fetch_tushare_indices() -> tuple[list[MarketIndex], dict]:
    try:
        import tushare as ts
    except ImportError:
        return [], {"status": "error", "source": "empty", "message": "tushare 未安装，请检查 requirements.txt。"}

    try:
        symbols = [symbol for symbol, _, _ in TUSHARE_INDEX_TARGETS]
        frame = ts.get_realtime_quotes(symbols)
    except Exception as exc:
        return [], {"status": "error", "source": "empty", "message": sanitize_message(type(exc).__name__)}

    if frame is None or frame.empty:
        return [], {"status": "empty", "source": "empty", "message": "tushare 暂无可用行情。"}

    rows: list[MarketIndex] = []
    updated_at = datetime.now()
    for symbol, fallback_name, region in TUSHARE_INDEX_TARGETS:
        matched = frame[frame.get("code", "").astype(str) == symbol] if "code" in frame.columns else frame.iloc[0:0]
        if matched.empty:
            continue
        row = matched.iloc[0]
        price = _to_float(row.get("price"))
        change = _to_float(row.get("change"))
        change_pct = _to_float(row.get("p_change"))
        if change is None and price is not None:
            previous = _to_float(row.get("pre_close"))
            change = price - previous if previous is not None else None
        rows.append(
            MarketIndex(
                symbol=symbol,
                name=str(row.get("name") or fallback_name),
                region=region,
                price=price,
                change=change,
                change_pct=change_pct,
                turnover=_to_float(row.get("amount")),
                source=TUSHARE_SOURCE,
                updated_at=updated_at,
                status="success",
                message="tushare 开源实时行情。",
            )
        )

    if not rows:
        return [], {"status": "empty", "source": "empty", "message": "tushare 未返回目标指数。"}
    return rows, {"status": "success", "source": "tushare", "message": "tushare 数据可用。"}


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
