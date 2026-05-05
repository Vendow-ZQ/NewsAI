"""GitHub Trending 信息源采集。"""

import re
import time
import requests
from datetime import datetime
from typing import Any
from bs4 import BeautifulSoup

from core.sources.base import BaseSource


class GitHubTrendingSource(BaseSource):
    """GitHub Trending项目采集源。

    通过解析GitHub Trending页面HTML获取热门项目。
    支持重试机制和错误处理。
    """

    name = "GitHub"
    TRENDING_URL = "https://github.com/trending/{language}?since={since}"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def fetch(self, limit: int = 5, config: dict = None) -> list[dict[str, Any]]:
        """获取GitHub Trending项目。

        Args:
            limit: 最大获取数量
            config: 配置字典，支持:
                - language: 编程语言，默认"python"
                - since: 时间范围，默认"daily" (daily/weekly/monthly)

        Returns:
            标准格式的项目列表
        """
        config = config or {}
        language = config.get("language", "python")
        since = config.get("since", "daily")

        url = self.TRENDING_URL.format(language=language, since=since)

        # 获取页面内容
        html = self._fetch_page(url)
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = []

            # 查找所有 trending 项目
            # GitHub Trending 页面结构
            # 确保limit是整数
            limit = int(limit) if limit else 20
            articles = list(soup.find_all('article', class_='Box-row'))[:limit]

            for article in articles:
                try:
                    # 提取项目信息
                    result = self._parse_repo(article, language)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"[GitHub] 解析项目失败: {e}")
                    continue

            print(f"[GitHub] 成功获取 {len(results)} 个Trending项目")
            return results

        except Exception as e:
            print(f"[GitHub] 解析页面失败: {e}")
            return []

    def _fetch_page(self, url: str) -> str:
        """获取页面HTML内容。"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"[GitHub] 请求失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    return ""
        return ""

    def _parse_repo(self, article: BeautifulSoup, language: str) -> dict:
        """解析单个项目信息。"""
        # 提取项目名称
        h2 = article.find('h2')
        if not h2:
            return None

        # 获取repo完整名 (user/repo)
        repo_name = h2.get_text(strip=True).replace(' ', '').replace('\n', '')

        # 提取链接
        link_elem = h2.find('a')
        if not link_elem:
            return None

        repo_url = "https://github.com" + link_elem.get('href', '')

        # 提取描述
        description = ""
        p_elem = article.find('p', class_='col-9')
        if p_elem:
            description = p_elem.get_text(strip=True)

        # 提取stars数
        stars_text = "0"
        stars_elem = article.find('a', class_=re.compile('Link--muted'))
        if stars_elem:
            stars_text = stars_elem.get_text(strip=True)

        # 解析stars数字
        stars = self._parse_stars(stars_text)

        # 提取今日新增stars
        stars_today = "0"
        today_elem = article.find('span', class_=re.compile('d-inline-block.*float-sm-right'))
        if today_elem:
            stars_today_text = today_elem.get_text(strip=True)
            match = re.search(r'(\d+)', stars_today_text.replace(',', ''))
            if match:
                stars_today = match.group(1)

        # 构建标准格式
        return {
            "标题": repo_name,
            "原文链接": repo_url,
            "原文摘要": description,
            "原文语言": "英文",
            "发布时间": datetime.now().isoformat(),
            "信源平台": "GitHub",
            # 额外字段
            "编程语言": language,
            "stars": stars,
            "今日新增": stars_today,
        }

    def _parse_stars(self, stars_text: str) -> int:
        """解析stars数字。"""
        try:
            # 处理 "1.2k" 格式
            stars_text = stars_text.replace(',', '').lower()
            if 'k' in stars_text:
                return int(float(stars_text.replace('k', '')) * 1000)
            elif 'm' in stars_text:
                return int(float(stars_text.replace('m', '')) * 1000000)
            else:
                return int(stars_text)
        except:
            return 0
