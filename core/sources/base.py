"""BaseSource 抽象 -- 信息源采集基类。"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSource(ABC):
    """信息源基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        """采集最新条目，返回标准化字典列表。"""
        ...
