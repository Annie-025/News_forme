from __future__ import annotations

from pathlib import Path

import yaml


def load_sources(path: Path) -> dict[str, list[dict]]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}
