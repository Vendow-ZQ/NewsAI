"""小审 -- 审核员 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    description = "审核员：事实核查与合规审核"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: LLM 审核内容
        return state
