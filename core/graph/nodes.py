"""LangGraph 节点函数 -- 包装 Agent 为图节点。"""

from typing import Any, Dict

from core.graph.state import NewsAIState
from core.agents.trend_scout import TrendScoutAgent
from core.agents.topic_curator import TopicCuratorAgent
from core.agents.content_writer import ContentWriterAgent
from core.agents.visual_designer import VisualDesignerAgent
from core.agents.script_writer import ScriptWriterAgent
from core.agents.reviewer import ReviewerAgent
from core.agents.editor import EditorAgent
from core.agents.distributor import DistributorAgent
from core.agents.analyst import AnalystAgent


def _make_log(agent: str, status: str, **kwargs) -> list:
    """创建单条执行日志（用于Annotated合并）"""
    return [{"agent": agent, "status": status, **kwargs}]


def _agent_context(state: NewsAIState) -> dict:
    """构建Agent执行上下文，统一传递topic_id和asset_id。"""
    ctx = {}
    if state.current_topic_id:
        ctx["topic_id"] = state.current_topic_id
    if state.current_asset_id:
        ctx["asset_id"] = state.current_asset_id
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
            # 更新 state：选中 topic_id 和 asset_id
            topic_id = result.get("selected_topic_id")
            asset_id = result.get("asset_id")
            return {
                "execution_log": _make_log("小编", "完成", result=result),
                "current_topic_id": topic_id,
                "current_asset_id": asset_id,
            }
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


# production_sync 节点（v3 新增）
def create_production_sync_node(storage: Any, llm: Any):
    """创建 production_sync 节点（生产组状态同步）。

    检查 ASSET 表中 3 个生产状态是否都为"已完成"。
    如果是，更新 TOPIC 状态为"审改中"，ASSET 生产完成时间。
    """
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            asset_id = state.current_asset_id
            if not asset_id:
                return {"execution_log": _make_log("production_sync", "跳过", reason="无 asset_id")}

            # 读取 ASSET 记录
            asset = storage.get_by_id("内容资产库", asset_id)
            if not asset:
                return {"execution_log": _make_log("production_sync", "失败", reason="ASSET 不存在")}

            asset_data = asset.data
            text_status = asset_data.get("文案状态", "")
            image_status = asset_data.get("配图状态", "")
            video_status = asset_data.get("视频状态", "")

            all_done = (text_status == "已完成" and image_status == "已完成" and video_status == "已完成")

            if all_done:
                from core.agents.base import current_timestamp_ms
                # 更新 ASSET
                storage.update("内容资产库", asset_id, {
                    "生产完成时间": current_timestamp_ms(),
                })
                # 更新 TOPIC
                topic_id = state.current_topic_id
                if topic_id:
                    storage.update("选题库", topic_id, {
                        "选题状态": "审改中",
                    })
                print(f"[production_sync] 3 个生产状态全完成，触发审改阶段")
                return {"execution_log": _make_log("production_sync", "完成", all_done=True)}
            else:
                print(f"[production_sync] 等待中: 文案={text_status}, 配图={image_status}, 视频={video_status}")
                return {"execution_log": _make_log("production_sync", "等待", all_done=False)}
        except Exception as e:
            return {"execution_log": _make_log("production_sync", "失败", error=str(e)), "errors": [str(e)]}
    return node


# 小审节点
def create_reviewer_node(storage: Any, llm: Any):
    """创建小审节点（审核）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = ReviewerAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            # 获取审查结果（reviewer返回的是单条结果）
            review_result = result.get("review_result", {})
            review_verdict = "需修改"  # 默认需修改，直到明确通过
            revision_count = state.revision_count
            # reviewer返回的是英文verdict: "pass" 或 "needs_revision"
            verdict = review_result.get("verdict", "needs_revision")
            if verdict == "pass":
                review_verdict = "通过"
            else:
                review_verdict = "需修改"
                revision_count += 1
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


# 小数节点
def create_analyst_node(storage: Any, llm: Any):
    """创建小数节点（复盘）。"""
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = AnalystAgent(storage, llm)
            result = agent.execute(_agent_context(state))
            return {"execution_log": _make_log("小数", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("小数", "失败", error=str(e)), "errors": [str(e)]}
    return node
