from __future__ import annotations

from data_sources.cache_store import response


def get_announcements_response() -> dict:
    return response(
        "success",
        "sample",
        [
            {
                "name": "巨潮资讯公告检索",
                "source": "CNINFO",
                "url": "https://www.cninfo.com.cn/new/disclosure",
                "type": "公告",
                "description": "",
                "tags": ["公告", "A股", "定期报告"],
            },
        ],
        "",
    )
