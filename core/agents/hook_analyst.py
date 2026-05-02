"""小析 -- 爆点分析 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class HookAnalystAgent(BaseAgent):
    name = "hook_analyst"
    description = "爆点分析：评估新闻的传播潜力与爆点"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: LLM 评估爆点分数
        return state
