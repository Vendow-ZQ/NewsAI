"""LangGraph 条件边逻辑。"""

from typing import Any


def should_continue_to_creation(state: dict[str, Any]) -> str:
    """判断是否有足够的选题进入创作阶段。"""
    topics = state.get("topics", [])
    if not topics:
        return "end"
    return "create"


def review_decision(state: dict[str, Any]) -> str:
    """审核通过 -> 分发，不通过 -> 重写。"""
    drafts = state.get("drafts", [])
    if all(d.get("review_status") == "approved" for d in drafts):
        return "distribute"
    return "rewrite"
