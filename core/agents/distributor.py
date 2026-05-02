"""小发 -- 分发策略 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class DistributorAgent(BaseAgent):
    name = "distributor"
    description = "分发策略：规划多平台分发方案"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: 生成分发策略
        return state
