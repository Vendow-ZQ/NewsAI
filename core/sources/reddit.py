"""Reddit 信息源采集（需 PRAW key）。"""

import os
import time
from datetime import datetime
from typing import Any

from core.sources.base import BaseSource


class RedditSource(BaseSource):
    """Reddit帖子采集源。

    使用PRAW库获取指定subreddit的帖子。
    支持环境变量配置和graceful degradation。
    """

    name = "Reddit"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # 默认subreddit和排序方式
    DEFAULT_SUBREDDIT = "LocalLLaMA"
    DEFAULT_SORT = "hot"

    def fetch(self, limit: int = 5, config: dict = None) -> list[dict[str, Any]]:
        """获取Reddit帖子。

        Args:
            limit: 最大获取数量
            config: 配置字典，支持:
                - subreddit: subreddit名称，默认"LocalLLaMA"
                - sort: 排序方式，默认"hot" (hot/top/new)

        Returns:
            标准格式的帖子列表，如果未配置API则返回空列表
        """
        config = config or {}
        subreddit = config.get("subreddit", self.DEFAULT_SUBREDDIT)
        sort = config.get("sort", self.DEFAULT_SORT)

        # 检查环境变量
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "NewsAI/0.1")

        if not client_id or not client_secret:
            print(f"[Reddit] 警告: 未配置Reddit API密钥 (REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET)，跳过采集")
            return []

        try:
            import praw
        except ImportError:
            print(f"[Reddit] 警告: praw库未安装，跳过采集")
            return []

        # 初始化PRAW
        for attempt in range(self.MAX_RETRIES):
            try:
                reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                )

                # 获取subreddit
                sub = reddit.subreddit(subreddit)

                # 根据排序方式获取帖子
                if sort == "hot":
                    posts = sub.hot(limit=limit)
                elif sort == "top":
                    posts = sub.top(limit=limit)
                elif sort == "new":
                    posts = sub.new(limit=limit)
                else:
                    posts = sub.hot(limit=limit)

                results = []
                for post in posts:
                    try:
                        # 解析时间
                        created_at = datetime.fromtimestamp(post.created_utc).isoformat()

                        # 构建标准格式
                        result = {
                            "标题": post.title,
                            "原文链接": f"https://reddit.com{post.permalink}",
                            "原文摘要": post.selftext[:500] if post.selftext else "",
                            "原文语言": "英文",
                            "发布时间": created_at,
                            "信源平台": "Reddit",
                            # 额外字段
                            "作者": post.author.name if post.author else "[deleted]",
                            "分数": post.score,
                            "评论数": post.num_comments,
                            "外部链接": post.url if not post.is_self else "",
                            "subreddit": subreddit,
                        }
                        results.append(result)

                    except Exception as e:
                        print(f"[Reddit] 解析帖子失败: {e}")
                        continue

                print(f"[Reddit] 成功获取 {len(results)} 条帖子 from r/{subreddit}")
                return results

            except Exception as e:
                print(f"[Reddit] 请求失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    return []

        return []
