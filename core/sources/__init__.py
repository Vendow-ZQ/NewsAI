"""信源采集模块。

提供统一的信息源获取接口，支持多种平台：
- 真实爬虫: arXiv, HackerNews, GitHub Trending
- Mock数据: 小红书, 抖音, X(Twitter)
"""

from core.sources.arxiv import ArxivSource
from core.sources.hackernews import HackerNewsSource
from core.sources.github_trending import GitHubTrendingSource
from core.sources.reddit import RedditSource
from core.sources.mock_xiaohongshu import MockXiaohongshuSource
from core.sources.mock_douyin import MockDouyinSource
from core.sources.mock_x import MockXSource

# 全局缓存，避免重复创建实例
_source_instances = {}


def get_source(platform: str):
    """获取对应平台的信息源实例。

    Args:
        platform: 平台名称，支持：
            - "arXiv" - 学术论文
            - "HackerNews" - 技术新闻
            - "GitHub" - 开源项目趋势
            - "小红书" - 社交媒体（Mock）
            - "抖音" - 短视频平台（Mock）
            - "X" - Twitter（Mock）

    Returns:
        BaseSource 实例，如果平台不存在则返回 None

    Example:
        >>> source = get_source("arXiv")
        >>> items = source.fetch(limit=5)

    Supported platforms:
        - "arXiv" - 学术论文
        - "HackerNews" - 技术新闻
        - "GitHub" - 开源项目趋势
        - "Reddit" - 社区讨论
        - "小红书" - 社交媒体（Mock）
        - "抖音" - 短视频平台（Mock）
        - "X" - Twitter（Mock）
    """
    # 标准化平台名称
    platform_map = {
        "arxiv": "arXiv",
        "hackernews": "HackerNews",
        "github": "GitHub",
        "github_trending": "GitHub",
        "reddit": "Reddit",
        "xiaohongshu": "小红书",
        "douyin": "抖音",
        "x": "X",
        "twitter": "X",
    }
    normalized = platform_map.get(platform.lower(), platform)

    # 缓存实例
    if normalized in _source_instances:
        return _source_instances[normalized]

    sources = {
        "arXiv": ArxivSource,
        "HackerNews": HackerNewsSource,
        "GitHub": GitHubTrendingSource,
        "Reddit": RedditSource,
        "小红书": MockXiaohongshuSource,
        "抖音": MockDouyinSource,
        "X": MockXSource,
    }

    source_class = sources.get(normalized)
    if source_class:
        instance = source_class()
        _source_instances[normalized] = instance
        return instance

    return None


def list_supported_sources() -> list[str]:
    """返回所有支持的平台列表。"""
    return ["arXiv", "HackerNews", "GitHub", "Reddit", "小红书", "抖音", "X"]


def clear_source_cache():
    """清除信源实例缓存。

    主要用于测试场景，确保每次获取新实例。
    """
    _source_instances.clear()
