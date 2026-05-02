"""小文 -- 文字编辑 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class ContentWriterAgent(BaseAgent):
    name = "content_writer"
    description = "文字编辑：撰写适配不同平台的中文内容"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: LLM 生成平台内容
        return state
