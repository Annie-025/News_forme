from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from data_sources.announcement_provider import get_announcements_response
from data_sources.report_provider import get_reports_response
from src.market.market_service import get_market_response


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/market":
            self._send_json(get_market_response(DATA_DIR))
            return
        if path == "/api/reports":
            self._send_json(get_reports_response())
            return
        if path == "/api/announcements":
            self._send_json(get_announcements_response())
            return
        self._send_json({"status": "error", "source": "empty", "message": "接口不存在。", "data": None}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(to_jsonable(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="News For Me local JSON API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8510)
    args = parser.parse_args()
    server = HTTPServer((args.host, args.port), ApiHandler)
    print(f"News For Me API running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
