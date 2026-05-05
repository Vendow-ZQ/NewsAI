"""arXiv 信息源采集。"""

import time
import feedparser
import requests
from datetime import datetime
from typing import Any

from core.sources.base import BaseSource


class ArxivSource(BaseSource):
    """arXiv论文采集源。

    使用arXiv Atom API获取指定分类的最新论文。
    支持重试机制、错误处理和标准格式输出。
    """

    name = "arXiv"
    BASE_URL = "http://export.arxiv.org/api/query"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def fetch(self, limit: int = 5, config: dict = None) -> list[dict[str, Any]]:
        """获取arXiv论文列表。

        Args:
            limit: 最大获取数量
            config: 配置字典，支持:
                - category: 论文分类，默认"cs.AI"

        Returns:
            标准格式的论文列表，每条包含:
            - 标题: 论文标题
            - 原文链接: arXiv链接
            - 原文摘要: 论文摘要
            - 原文语言: "英文"
            - 发布时间: ISO8601格式
            - 信源平台: "arXiv"
        """
        config = config or {}
        category = config.get("category", "cs.AI")

        # 构建API URL
        url = f"{self.BASE_URL}?search_query=cat:{category}&sortBy=submittedDate&max_results={limit}"

        # 重试机制
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                print(f"[arXiv] 请求失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    print(f"[arXiv] 达到最大重试次数，返回空列表")
                    return []

        try:
            # 解析Atom feed
            feed = feedparser.parse(response.text)
            results = []

            # 确保entries是列表，可以安全切片
            # 强制转换limit为整数，防止字符串类型导致切片错误
            limit = int(limit) if limit else 5
            entries = list(feed.entries)[:limit]
            for entry in entries:
                try:
                    # 解析发布时间
                    published = entry.get("published", "")
                    if published:
                        # 转换为ISO8601格式
                        dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                        published_iso = dt.isoformat() + "Z"
                    else:
                        published_iso = datetime.now().isoformat()

                    # 提取作者信息
                    authors = []
                    if "authors" in entry:
                        authors = [author.get("name", "") for author in entry.authors]

                    # 构建标准格式
                    result = {
                        "标题": entry.get("title", "").replace("\n", " ").strip(),
                        "原文链接": entry.get("link", ""),
                        "原文摘要": entry.get("summary", "").replace("\n", " ").strip(),
                        "原文语言": "英文",
                        "发布时间": published_iso,
                        "信源平台": "arXiv",
                        # 额外字段
                        "作者": authors,
                        "分类": category,
                        "pdf链接": entry.get("pdf_link", ""),
                    }
                    results.append(result)

                except Exception as e:
                    print(f"[arXiv] 解析条目失败: {e}")
                    continue

            print(f"[arXiv] 成功获取 {len(results)} 条论文")
            return results

        except Exception as e:
            print(f"[arXiv] 解析feed失败: {e}")
            return []
