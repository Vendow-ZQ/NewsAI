"""Hacker News 信息源采集。"""

from typing import Any

import httpx

from core.sources.base import BaseSource

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


class HackerNewsSource(BaseSource):
    name = "hackernews"

    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(HN_TOP_URL)
            top_ids = resp.json()[:limit]

            results = []
            for item_id in top_ids:
                resp = await client.get(HN_ITEM_URL.format(item_id))
                item = resp.json()
                results.append({
                    "source": self.name,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": "",
                })
        return results
