"""小图 -- 视觉设计 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class VisualDesignerAgent(BaseAgent):
    name = "visual_designer"
    description = "视觉设计：生成文字卡片/信息图/AI 配图"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: 调用 visual 模块生成图片
        return state
