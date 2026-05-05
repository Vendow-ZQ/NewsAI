"""BaseSource 抽象 -- 信息源采集基类。"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSource(ABC):
    """信息源基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """信源名称。"""
        ...

    @abstractmethod
    def fetch(self, limit: int = 10, config: dict = None) -> list[dict[str, Any]]:
        """采集最新条目，返回标准化字典列表。

        Args:
            limit: 最大采集数量
            config: 额外配置参数

        Returns:
            标准化信息条目列表，每条包含：
            - title/标题: 信息标题
            - url/原文链接: 原文链接
            - summary/原文摘要: 内容摘要
            - source: 信源标识
        """
        ...
