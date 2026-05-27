from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.models import sanitize_message


def response(status: str, source: str, data: Any, message: str = "", updated_at: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "source": source,
        "updated_at": updated_at or datetime.now().isoformat(),
        "message": sanitize_message(message),
        "data": data,
    }


def read_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and "data" in payload:
        return payload
    return None


def write_cache(path: Path, data: Any, source: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = response("success", source, data, "实时数据已更新。")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def is_fresh(payload: dict[str, Any] | None, ttl_seconds: int, now: datetime | None = None) -> bool:
    if not payload or not payload.get("updated_at"):
        return False
    try:
        updated_at = datetime.fromisoformat(str(payload["updated_at"]))
    except ValueError:
        return False
    return ((now or datetime.now()) - updated_at).total_seconds() <= ttl_seconds


def load_or_refresh_json(
    cache_path: Path,
    *,
    ttl_seconds: int,
    loader: Callable[[], tuple[Any, str]],
    now: datetime | None = None,
) -> dict[str, Any]:
    cached = read_cache(cache_path)
    if is_fresh(cached, ttl_seconds, now):
        return response("success", "cache", cached.get("data"), "使用本地缓存。", cached.get("updated_at"))
    try:
        data, source = loader()
    except Exception as exc:
        if cached:
            return response("fallback", "cache", cached.get("data"), f"实时数据暂时不可用，已展示缓存。{type(exc).__name__}", cached.get("updated_at"))
        return response("error", "empty", None, f"实时数据暂时不可用。{type(exc).__name__}", None)
    return write_cache(cache_path, data, source)
