from __future__ import annotations

import sys

from src.market import market_providers as _market_providers

sys.modules[__name__] = _market_providers
