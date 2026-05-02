"""单例 ChatOpenAI 客户端 -- 指向火山方舟豆包 1.6。"""

import os
from functools import lru_cache

from langchain_openai import ChatOpenAI


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """返回全局共享的 LLM 客户端实例。"""
    return ChatOpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        model=os.getenv("LLM_MODEL", ""),
        temperature=0.7,
    )
