"""LangGraph 节点函数 -- 包装 Agent 为图节点。"""

from typing import Any, Dict

from core.graph.state import NewsAIState
from core.agents.trend_scout import TrendScoutAgent
from core.agents.topic_curator import TopicCuratorAgent
from core.agents.content_writer import ContentWriterAgent
from core.agents.visual_designer import VisualDesignerAgent
from core.agents.script_writer import ScriptWriterAgent
from core.agents.reviewer import ReviewerAgent
from core.agents.distributor import DistributorAgent


def _make_log(agent: str, status: str, **kwargs) -> list:
    """创建单条执行日志（用于Annotated合并）"""
    return [{"agent": agent, "status": status, **kwargs}]


# 小哨节点
def _agent_context(state: NewsAIState) -> dict:
    """构建Agent执行上下文，统一传递topic_id和koc_id。"""
    ctx = {}
    if state.current_topic_id:
        ctx["topic_id"] = state.current_topic_id
    if state.koc_id:
        ctx["koc_id"] = state.koc_id
    return ctx


# 小哨节点
def create_trend_scout_node(storage: Any, llm: Any):
    """创建小哨节点（信息采集）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = TrendScoutAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小哨", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小哨", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小编节点
def create_topic_curator_node(storage: Any, llm: Any):
    """创建小编节点（选题策划）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = TopicCuratorAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小编", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小编", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小文节点
def create_content_writer_node(storage: Any, llm: Any):
    """创建小文节点（内容撰写）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = ContentWriterAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小文", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小文", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小图节点
def create_visual_designer_node(storage: Any, llm: Any):
    """创建小图节点（视觉设计）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = VisualDesignerAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小图", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小图", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小播节点
def create_script_writer_node(storage: Any, llm: Any):
    """创建小播节点（视频脚本）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = ScriptWriterAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小播", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小播", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小审节点
def create_reviewer_node(storage: Any, llm: Any):
    """创建小审节点（审核）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = ReviewerAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            review_results = result.get("review_results", [])
            review_verdict = "通过"
            revision_count = state.revision_count
            # 处理多选题：任一需修改则整体需修改
            for rr in review_results:
                review_data = rr.get("review_result", {})
                verdict = review_data.get("审查结论", "需修改")
                if verdict == "需修改":
                    review_verdict = "需修改"
                    revision_count += 1
                    break
            return {
                "execution_log": _make_log("小审", "完成", verdict=review_verdict),
                "review_verdict": review_verdict,
                "revision_count": revision_count
            }
        except Exception as e:
            return {"execution_log": _make_log("小审", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小改节点
def create_editor_node(storage: Any, llm: Any):
    """创建小改节点（修改）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            from core.agents.editor import EditorAgent
            agent = EditorAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小改", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小改", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小发节点
def create_distributor_node(storage: Any, llm: Any):
    """创建小发节点（分发）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = DistributorAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小发", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小发", "失败", error=str(e)), "errors": [str(e)]}
    return node


def create_analyst_node(storage: Any, llm: Any):
    """创建小数节点（复盘）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            from core.agents.analyst import AnalystAgent
            agent = AnalystAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小数", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小数", "失败", error=str(e)), "errors": [str(e)]}
    return node
