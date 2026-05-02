"""文字卡片图 -- HTML 渲染 + Playwright 截图。"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


async def render_text_card(
    title: str,
    body: str,
    template: str = "card_white.html",
) -> bytes:
    """渲染文字卡片，返回 PNG 字节。"""
    # TODO: Playwright 渲染 HTML -> 截图
    raise NotImplementedError
