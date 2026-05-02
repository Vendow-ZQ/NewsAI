"""小播 -- 短视频编剧 Agent。"""

from typing import Any

from core.agents.base import BaseAgent


class ScriptWriterAgent(BaseAgent):
    name = "script_writer"
    description = "短视频编剧：生成短视频脚本与分镜"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO: LLM 生成短视频脚本
        return state
