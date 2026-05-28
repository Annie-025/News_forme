from __future__ import annotations

import sys

from src.market import market_service as _market_service

sys.modules[__name__] = _market_service
