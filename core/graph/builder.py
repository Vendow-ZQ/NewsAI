"""LangGraph 图构建工厂。"""

from langgraph.graph import StateGraph, END

from core.graph.state import GraphState
from core.graph import nodes


def build_graph() -> StateGraph:
    """构建并返回完整的新闻编辑流程图。"""
    graph = StateGraph(GraphState)

    # 添加节点
    graph.add_node("collect_news", nodes.collect_news)
    graph.add_node("analyze_hooks", nodes.analyze_hooks)
    graph.add_node("curate_topics", nodes.curate_topics)
    graph.add_node("write_content", nodes.write_content)
    graph.add_node("design_visuals", nodes.design_visuals)
    graph.add_node("write_script", nodes.write_script)
    graph.add_node("review_content", nodes.review_content)
    graph.add_node("distribute", nodes.distribute)
    graph.add_node("analyze_data", nodes.analyze_data)

    # 串联主流程
    graph.set_entry_point("collect_news")
    graph.add_edge("collect_news", "analyze_hooks")
    graph.add_edge("analyze_hooks", "curate_topics")
    graph.add_edge("curate_topics", "write_content")
    graph.add_edge("write_content", "design_visuals")
    graph.add_edge("design_visuals", "write_script")
    graph.add_edge("write_script", "review_content")
    graph.add_edge("review_content", "distribute")
    graph.add_edge("distribute", "analyze_data")
    graph.add_edge("analyze_data", END)

    return graph.compile()
