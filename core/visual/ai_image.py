"""AI 文生图 -- 即梦 API 调用。"""

import os

import httpx


async def generate_image(prompt: str) -> str | None:
    """调用即梦 API 生成图片，返回图片 URL。"""
    api_key = os.getenv("JIMENG_API_KEY")
    if not api_key:
        return None
    # TODO: 即梦 API 调用
    raise NotImplementedError
