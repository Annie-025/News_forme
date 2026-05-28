from config.settings import DATA_DIR
from src.market.market_service import *  # noqa: F401,F403
from src.market.market_service import get_market_response


def get_market_payload() -> dict:
    return get_market_response(DATA_DIR)
