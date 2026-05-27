from __future__ import annotations

from data_sources.cache_store import response


def get_reports_response() -> dict:
    return response(
        "success",
        "sample",
        [
            {
                "name": "东方财富研报中心",
                "source": "Eastmoney",
                "url": "https://data.eastmoney.com/report/",
                "type": "研报",
                "description": "",
                "tags": ["研报", "行业", "公司"],
            },
        ],
        "",
    )
