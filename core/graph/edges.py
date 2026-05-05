"""LangGraph 条件边逻辑。"""

from core.graph.state import NewsAIState


def should_continue_review(state: NewsAIState) -> str:
    """判断是否继续审改循环。

    如果审改轮次小于最大轮次且审查结论为"需修改"，则继续审改。
    否则，审改完成。

    Returns:
        "继续审改" 或 "审改完成"
    """
    if state.revision_count < state.max_revisions and state.review_verdict == "需修改":
        return "继续审改"
    return "审改完成"
