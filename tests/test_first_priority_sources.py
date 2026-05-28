from __future__ import annotations

from datetime import datetime

from src.models import MarketIndex


def test_market_response_falls_back_to_tushare_when_akshare_empty(tmp_path, monkeypatch):
    import data_sources.market_service as market_service

    monkeypatch.setattr(market_service, "fetch_market_indices", lambda: [])

    class EmptySnapshot:
        a_spot_top = []
        index_spot = []
        concept_boards = []
        fund_flow = []
        market_activity = []
        limit_up_pool = []
        errors = []
        source_status = []
        updated_at = None

    monkeypatch.setattr(market_service, "fetch_akshare_snapshot", lambda limit=8: EmptySnapshot())
    monkeypatch.setattr(
        market_service,
        "fetch_tushare_indices",
        lambda: (
            [
                MarketIndex(
                    symbol="000001.SH",
                    name="上证指数",
                    region="CN",
                    price=3100.0,
                    change=10.0,
                    change_pct=0.32,
                    turnover=1200.0,
                    source="tushare",
                    updated_at=datetime(2026, 5, 27, 15, 0),
                    status="success",
                    message="mock",
                )
            ],
            {"status": "success", "source": "tushare", "message": "ok"},
        ),
    )

    payload = market_service.get_market_response(tmp_path, ttl_seconds=0)

    assert payload["status"] == "success"
    assert payload["source"] == "tushare"
    assert payload["data"]["indices"][0].source == "tushare"


def test_tushare_provider_does_not_require_token(monkeypatch):
    import data_sources.tushare_provider as tushare_provider

    class FakeTushare:
        @staticmethod
        def get_realtime_quotes(symbols):
            import pandas as pd

            return pd.DataFrame(
                [
                    {
                        "code": "sh",
                        "name": "上证指数",
                        "price": "3100.0",
                        "pre_close": "3090.0",
                        "change": "10.0",
                        "p_change": "0.32",
                        "amount": "1200",
                    }
                ]
            )

    import sys

    monkeypatch.delenv("TUSHARE" + "_TOKEN", raising=False)
    monkeypatch.setitem(sys.modules, "tushare", FakeTushare)

    rows, status = tushare_provider.fetch_tushare_indices()

    assert status["status"] == "success"
    assert rows[0].source == "tushare"


def test_report_endpoint_payload_contains_eastmoney_entry():
    from data_sources.report_provider import get_reports_response

    payload = get_reports_response()

    assert payload["status"] == "success"
    assert any("eastmoney.com/report" in row["url"] for row in payload["data"])


def test_announcement_endpoint_payload_contains_cninfo_entry():
    from data_sources.announcement_provider import get_announcements_response

    payload = get_announcements_response()
    urls = " ".join(row["url"] for row in payload["data"])

    assert payload["status"] == "success"
    assert "cninfo.com.cn" in urls
    assert "cninfo.com.cn" in urls


def test_api_json_serializer_handles_market_models():
    from api_server import to_jsonable

    payload = {
        "data": {
            "indices": [
                MarketIndex(
                    symbol="000001.SH",
                    name="上证指数",
                    region="CN",
                    price=3100.0,
                    change=None,
                    change_pct=None,
                    turnover=None,
                    source="tushare",
                    updated_at=datetime(2026, 5, 27, 15, 0),
                    status="success",
                )
            ]
        }
    }

    converted = to_jsonable(payload)

    assert converted["data"]["indices"][0]["updated_at"] == "2026-05-27T15:00:00"
