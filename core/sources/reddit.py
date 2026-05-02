"""Reddit 信息源采集（需 PRAW key）。"""

import os
from typing import Any

from core.sources.base import BaseSource


class RedditSource(BaseSource):
    name = "reddit"

    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        if not client_id:
            return []

        import praw

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "newsai/0.1"),
        )
        results = []
        for post in reddit.subreddit("artificial").hot(limit=limit):
            results.append({
                "source": self.name,
                "title": post.title,
                "url": f"https://reddit.com{post.permalink}",
                "summary": post.selftext[:500] if post.selftext else "",
            })
        return results
