"""小编 -- 选题生成 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class TopicCuratorAgent(BaseAgent):
    name = "topic_curator"
    description = "选题生成：根据爆点排序生成选题方案"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: 基于爆点排序生成选题
        return state
