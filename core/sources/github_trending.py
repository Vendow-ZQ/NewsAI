"""GitHub Trending 信息源采集。"""

from typing import Any

import httpx

from core.sources.base import BaseSource

GITHUB_TRENDING_URL = "https://api.github.com/search/repositories"


class GitHubTrendingSource(BaseSource):
    name = "github_trending"

    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GITHUB_TRENDING_URL,
                params={
                    "q": "topic:ai created:>2026-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": limit,
                },
            )
            data = resp.json()

        results = []
        for repo in data.get("items", [])[:limit]:
            results.append({
                "source": self.name,
                "title": repo.get("full_name", ""),
                "url": repo.get("html_url", ""),
                "summary": repo.get("description", ""),
            })
        return results
