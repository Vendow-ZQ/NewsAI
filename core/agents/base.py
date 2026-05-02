"""BaseAgent 抽象类 -- 所有 Agent 的基类。"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """所有 Agent 的抽象基类。

    每个 Agent 接收 tools 列表（由 adapter 层注入），
    实现 run() 方法处理输入状态并返回更新。
    """

    def __init__(self, tools: list | None = None):
        self.tools = tools or []

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 职责描述。"""
        ...

    @abstractmethod
    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 逻辑，返回状态更新。"""
        ...
