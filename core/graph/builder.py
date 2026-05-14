"""LangGraph 图构建工厂 - v3.0。

流程：
1. 小哨（信息采集）→ 小编（选题策划）
2. Fan-out: 小编并发到生产组3人（小文、小图、小播）
3. Fan-in: 3人完成后到 production_sync（状态同步）
4. production_sync → 小审
5. 审改循环：小审 → 小改 → 小审（最多3轮）
6. 小发（分发）→ 小数（复盘）→ 结束
"""

from langgraph.graph import StateGraph, END
from typing import Any

from core.graph.state import NewsAIState
from core.graph.nodes import (
    create_trend_scout_node,
    create_topic_curator_node,
    create_content_writer_node,
    create_visual_designer_node,
    create_script_writer_node,
    create_production_sync_node,
    create_reviewer_node,
    create_editor_node,
    create_distributor_node,
)
from core.graph.edges import should_continue_review


def build_newsai_graph(storage: Any, llm: Any):
    """构建并返回完整的 NewsAI 新闻编辑流程图。

    Args:
        storage: 存储实例（如 FeishuStorage）
        llm: LLM 客户端实例

    Returns:
        编译后的 StateGraph 实例
    """
    workflow = StateGraph(NewsAIState)

    # 添加所有节点
    workflow.add_node("小哨", create_trend_scout_node(storage, llm))
    workflow.add_node("小编", create_topic_curator_node(storage, llm))
    workflow.add_node("小文", create_content_writer_node(storage, llm))
    workflow.add_node("小图", create_visual_designer_node(storage, llm))
    workflow.add_node("小播", create_script_writer_node(storage, llm))
    workflow.add_node("production_sync", create_production_sync_node(storage, llm))
    workflow.add_node("小审", create_reviewer_node(storage, llm))
    workflow.add_node("小改", create_editor_node(storage, llm))
    workflow.add_node("小发", create_distributor_node(storage, llm))

    # 设置入口
    workflow.set_entry_point("小哨")

    # 顺序边：小哨 → 小编
    workflow.add_edge("小哨", "小编")

    # v3.1 改造：小编 → 小文（串行第1人）
    workflow.add_edge("小编", "小文")

    # v3.1 改造：小文完成后 fan-out 到小图+小播（基于小文长文翻译）
    workflow.add_edge("小文", "小图")
    workflow.add_edge("小文", "小播")

    # Fan-in: 小图+小播完成后到 production_sync
    workflow.add_edge("小图", "production_sync")
    workflow.add_edge("小播", "production_sync")

    # production_sync → 小审
    workflow.add_edge("production_sync", "小审")

    # 审改循环
    workflow.add_conditional_edges(
        "小审",
        should_continue_review,
        {"继续审改": "小改", "审改完成": "小发"}
    )
    workflow.add_edge("小改", "小审")

    # 小发 后直接结束（小数拆分为独立流程）
    workflow.add_edge("小发", END)

    return workflow.compile()
