from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_local_env(root: Path) -> None:
    if load_dotenv:
        load_dotenv(root / ".env")


def env_value(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in env_value(name, default).split(",") if item.strip()]
