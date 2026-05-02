"""小哨 -- 信息采集 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class TrendScoutAgent(BaseAgent):
    name = "trend_scout"
    description = "信息采集：从多个信息源抓取最新 AI 动态"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: 调用 sources 采集信息
        return state
