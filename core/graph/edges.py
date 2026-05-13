"""LangGraph 条件边逻辑 - v3.0。"""

from core.graph.state import NewsAIState


def should_continue_review(state: NewsAIState) -> str:
    """判断是否继续审改循环。

    v3.0 逻辑：
    - 如果审改轮次 >= 最大轮次（3），强制完成
    - 如果审查结论为"需修改"且轮次 < 最大轮次，继续审改
    - 否则，审改完成

    Returns:
        "继续审改" 或 "审改完成"
    """
    # 强制通过：达到最大轮次
    if state.revision_count >= state.max_revisions:
        print(f"[审改循环] 已达最大轮次 {state.max_revisions}，强制通过")
        return "审改完成"

    # 正常判断
    if state.review_verdict == "需修改" and state.revision_count < state.max_revisions:
        print(f"[审改循环] 第 {state.revision_count + 1} 轮审改")
        return "继续审改"

    print(f"[审改循环] 审查通过，进入分发阶段")
    return "审改完成"
