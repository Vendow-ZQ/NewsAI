"""LangGraph 端到端冒烟测试。"""

import pytest


def test_graph_builds():
    """测试 Graph 能否正常构建。"""
    from core.graph.builder import build_graph

    graph = build_graph()
    assert graph is not None


def test_state_model():
    """测试 State 模型能否正常实例化。"""
    from core.graph.state import GraphState

    state = GraphState()
    assert state.raw_news == []
    assert state.current_step == ""
