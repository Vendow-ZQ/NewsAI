"""LangGraph 端到端冒烟测试。"""

import pytest


def test_graph_builds():
    """测试 Graph 能否正常构建。"""
    from core.graph.builder import build_newsai_graph

    graph = build_newsai_graph(None, None)
    assert graph is not None


def test_state_model():
    """测试 State 模型能否正常实例化。"""
    from core.graph.state import NewsAIState

    state = NewsAIState()
    assert state.current_topic_id is None
    assert state.revision_count == 0
    assert state.koc_id == "KOC-001"
