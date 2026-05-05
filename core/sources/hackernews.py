"""Hacker News 信息源采集。"""

import time
import requests
from datetime import datetime
from typing import Any

from core.sources.base import BaseSource


class HackerNewsSource(BaseSource):
    """Hacker News热门帖子采集源。

    使用Firebase API获取热门帖子，支持关键词过滤和重试机制。
    """

    name = "HackerNews"
    TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
    ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # AI相关默认关键词
    DEFAULT_KEYWORDS = [
        "AI", "LLM", "artificial intelligence", "machine learning", "deep learning",
        "neural network", "GPT", "ChatGPT", "Claude", "OpenAI", "Anthropic",
        "model", "training", "fine-tune", "transformer", "language model"
    ]

    def fetch(self, limit: int = 5, config: dict = None) -> list[dict[str, Any]]:
        """获取Hacker News热门帖子。

        Args:
            limit: 最大获取数量
            config: 配置字典，支持:
                - keywords: 过滤关键词列表
                - require_comments: 是否要求有评论
                - min_score: 最低分数

        Returns:
            标准格式的帖子列表
        """
        config = config or {}
        keywords = config.get("keywords", self.DEFAULT_KEYWORDS)
        min_score = config.get("min_score", 0)
        require_comments = config.get("require_comments", False)

        # 获取top stories ID列表
        top_ids = self._fetch_top_stories()
        if not top_ids:
            return []

        # 强制转换limit为整数，防止字符串类型导致比较错误
        limit = int(limit) if limit else 5
        results = []
        for item_id in top_ids:
            if len(results) >= limit:
                break

            item = self._fetch_item(item_id)
            if not item:
                continue

            # 过滤死掉的帖子或没有URL的帖子
            if item.get("dead") or item.get("deleted"):
                continue

            # 应用过滤器
            if not self._should_include(item, keywords, min_score, require_comments):
                continue

            # 解析时间
            timestamp = item.get("time", 0)
            posted_at = datetime.fromtimestamp(timestamp).isoformat() if timestamp else datetime.now().isoformat()

            # 构建标准格式
            result = {
                "标题": item.get("title", ""),
                "原文链接": item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                "原文摘要": f"Score: {item.get('score', 0)}, Comments: {item.get('descendants', 0)}",
                "原文语言": "英文",
                "发布时间": posted_at,
                "信源平台": "HackerNews",
                # 额外字段
                "作者": item.get("by", ""),
                "分数": item.get("score", 0),
                "评论数": item.get("descendants", 0),
                "hn链接": f"https://news.ycombinator.com/item?id={item_id}",
            }
            results.append(result)

        print(f"[HackerNews] 成功获取 {len(results)} 条帖子")
        return results

    def _fetch_top_stories(self) -> list[int]:
        """获取热门帖子ID列表。"""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(self.TOP_STORIES_URL, timeout=30)
                response.raise_for_status()
                return response.json()[:100]  # 获取前100个
            except requests.exceptions.RequestException as e:
                print(f"[HackerNews] 获取top stories失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    return []
        return []

    def _fetch_item(self, item_id: int) -> dict:
        """获取单个帖子详情。"""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(self.ITEM_URL.format(item_id), timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"[HackerNews] 获取item {item_id}失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    return {}
        return {}

    def _should_include(self, item: dict, keywords: list, min_score: int, require_comments: bool) -> bool:
        """判断帖子是否应该被包含。"""
        # 检查分数，确保是整数类型
        score = item.get("score", 0)
        if isinstance(score, str):
            try:
                score = int(score)
            except:
                score = 0
        if score < min_score:
            return False

        # 检查评论要求
        if require_comments and item.get("descendants", 0) == 0:
            return False

        # 如果没有关键词，包含所有
        if not keywords:
            return True

        # 检查标题是否包含关键词
        title = item.get("title", "").lower()
        return any(kw.lower() in title for kw in keywords)
