"""arXiv 信息源采集。"""

from typing import Any

import feedparser

from core.sources.base import BaseSource

ARXIV_FEED_URL = "https://export.arxiv.org/rss/cs.AI"


class ArxivSource(BaseSource):
    name = "arxiv"

    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        feed = feedparser.parse(ARXIV_FEED_URL)
        results = []
        for entry in feed.entries[:limit]:
            results.append({
                "source": self.name,
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", ""),
            })
        return results
