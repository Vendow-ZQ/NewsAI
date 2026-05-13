"""单例 ChatOpenAI 客户端 -- 指向火山方舟豆包 1.6。

切换Mock模式：在 .env 中设置 LLM_MOCK=1
"""

import os
from functools import lru_cache

from langchain_openai import ChatOpenAI


@lru_cache(maxsize=1)
def get_llm():
    """返回全局共享的 LLM 客户端实例。"""
    # Mock模式：绕过真实API，用于pipeline验证
    if os.getenv("LLM_MOCK", "") == "1":
        from core.llm.mock_client import MockLLM
        return MockLLM()

    return ChatOpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        model=os.getenv("LLM_MODEL", ""),
        temperature=0.7,
        timeout=120,
        max_retries=1,
    )
