from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.models import AkShareSnapshot, SourceStatus, sanitize_message


AK_SOURCE = "AKShare / 东方财富"
CN_INDEX_SYMBOL_GROUPS = ["沪深重要指数", "上证系列指数", "深证系列指数", "中证系列指数"]


def safe_ak_call(func_name: str, *args, **kwargs) -> tuple[pd.DataFrame, SourceStatus]:
    updated_at = datetime.now()
    try:
        import akshare as ak
    except ImportError:
        return pd.DataFrame(), SourceStatus("AKShare", False, "error", "AKShare 未安装，请检查 requirements.txt。", updated_at)

    func = getattr(ak, func_name, None)
    if func is None:
        return pd.DataFrame(), SourceStatus(func_name, True, "error", f"AKShare 接口不存在：{func_name}", updated_at)

    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        return pd.DataFrame(), SourceStatus(func_name, True, "error", f"{type(exc).__name__}: {sanitize_message(str(exc))}", updated_at)

    if result is None:
        return pd.DataFrame(), SourceStatus(func_name, True, "empty", "AKShare 返回空结果。", updated_at)
    if not isinstance(result, pd.DataFrame):
        return pd.DataFrame(), SourceStatus(func_name, True, "error", "AKShare 返回数据格式不是 DataFrame。", updated_at)
    if result.empty:
        return result, SourceStatus(func_name, True, "empty", "AKShare 暂无数据。", updated_at)
    return result, SourceStatus(func_name, True, "success", "成功", updated_at)


def fetch_cn_index_spot() -> tuple[pd.DataFrame, SourceStatus]:
    frames: list[pd.DataFrame] = []
    statuses: list[SourceStatus] = []
    for symbol in CN_INDEX_SYMBOL_GROUPS:
        frame, status = safe_ak_call("stock_zh_index_spot_em", symbol=symbol)
        statuses.append(status)
        if not frame.empty:
            frames.append(frame)

    updated_at = datetime.now()
    successes = [status for status in statuses if status.status == "success"]
    if not frames:
        if any(status.status == "error" for status in statuses):
            message = "；".join(status.message for status in statuses if status.status == "error")[:220]
            return pd.DataFrame(), SourceStatus("AKShare CN indices", True, "error", message, updated_at)
        return pd.DataFrame(), SourceStatus("AKShare CN indices", True, "empty", "AKShare 暂无中国指数数据。", updated_at)

    merged = pd.concat(frames, ignore_index=True)
    dedupe_cols = [column for column in ["代码", "名称"] if column in merged.columns]
    if dedupe_cols:
        merged = merged.drop_duplicates(subset=dedupe_cols, keep="first")

    if len(successes) == len(statuses):
        return merged, SourceStatus("AKShare CN indices", True, "success", "成功", updated_at)
    return merged, SourceStatus("AKShare CN indices", True, "fallback", "部分 AKShare 指数接口失败，已显示可用数据。", updated_at)


def fetch_akshare_snapshot(limit: int = 8) -> AkShareSnapshot:
    updated_at = datetime.now()
    source_status: list[SourceStatus] = []
    a_spot_top = _call_top_rows(source_status, "stock_zh_a_spot_em", limit, ["代码", "名称", "最新价", "涨跌幅", "成交额"])
    index_spot = _call_top_rows(source_status, "stock_zh_index_spot_em", limit, ["代码", "名称", "最新价", "涨跌幅", "成交额"], symbol="沪深重要指数")
    concept_boards = _call_top_rows(source_status, "stock_board_concept_name_em", limit, ["板块名称", "涨跌幅", "总市值", "上涨家数", "下跌家数"])
    fund_flow = _call_top_rows(source_status, "stock_sector_fund_flow_rank", limit, ["名称", "今日涨跌幅", "今日主力净流入-净额", "今日主力净流入-净占比"], indicator="今日", sector_type="概念资金流")
    market_activity = _call_top_rows(source_status, "stock_market_activity_legu", limit, ["item", "value"])
    limit_up_pool = _call_top_rows(source_status, "stock_zt_pool_em", limit, ["代码", "名称", "涨跌幅", "最新价", "封板资金", "首次封板时间"], date=updated_at.strftime("%Y%m%d"))
    errors = [f"{status.name}: {status.message}" for status in source_status if status.status == "error"]
    return AkShareSnapshot(updated_at, a_spot_top, index_spot, limit_up_pool, concept_boards, fund_flow, market_activity, errors, source_status)


def snapshot_to_dict(snapshot: AkShareSnapshot) -> dict[str, Any]:
    return {
        "updated_at": snapshot.updated_at.isoformat() if snapshot.updated_at else None,
        "a_spot_top": snapshot.a_spot_top,
        "index_spot": snapshot.index_spot,
        "limit_up_pool": snapshot.limit_up_pool,
        "concept_boards": snapshot.concept_boards,
        "fund_flow": snapshot.fund_flow,
        "market_activity": snapshot.market_activity,
        "errors": snapshot.errors,
    }


def snapshot_from_dict(data: dict[str, Any]) -> AkShareSnapshot:
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])
        except ValueError:
            updated_at = None
    return AkShareSnapshot(
        updated_at=updated_at or datetime.now(),
        a_spot_top=data.get("a_spot_top", []),
        index_spot=data.get("index_spot", []),
        limit_up_pool=data.get("limit_up_pool", []),
        concept_boards=data.get("concept_boards", []),
        fund_flow=data.get("fund_flow", []),
        market_activity=data.get("market_activity", []),
        errors=data.get("errors", []),
        source_status=[],
    )


def _call_top_rows(source_status: list[SourceStatus], func_name: str, limit: int, preferred_columns: list[str], **kwargs) -> list[dict[str, Any]]:
    frame, status = safe_ak_call(func_name, **kwargs)
    source_status.append(status)
    return _top_rows(frame, limit, preferred_columns)


def _top_rows(df: pd.DataFrame, limit: int, preferred_columns: list[str]) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    columns = [column for column in preferred_columns if column in df.columns] or list(df.columns[: min(5, len(df.columns))])
    rows = df[columns].head(limit).where(pd.notna(df[columns]), "").to_dict("records")
    return [{str(key): _clean_value(value) for key, value in row.items()} for row in rows]


def _clean_value(value: Any) -> Any:
    return round(value, 2) if isinstance(value, float) else value
