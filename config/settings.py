from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"

DEFAULT_NEWS_LIMIT = 8
APP_TITLE = "News For Me"
APP_SUBTITLE = "个人财经信息工作台"
