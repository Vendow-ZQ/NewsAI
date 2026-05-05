"""LangGraph 共享 State 定义。"""

from dataclasses import dataclass, field
from typing import Optional, List, Annotated
import operator


@dataclass
class NewsAIState:
    """NewsAI LangGraph 状态类。

    用于在Agent节点之间传递状态信息。
    支持并发写入execution_log和errors（通过Annotated合并）。

    注意：current_topic_id不可在并行节点中修改，避免"Can receive only one value per step"错误。
    """
    current_topic_id: Optional[str] = None
    current_agent: Optional[str] = None
    revision_count: int = 0
    max_revisions: int = 3
    review_verdict: Optional[str] = None  # "通过" / "需修改"

    # 使用Annotated支持并发节点写入错误信息
    errors: Annotated[List[str], operator.add] = field(default_factory=list)

    # execution_log 使用 Annotated + operator.add 实现并发合并
    # 当多个节点并行返回execution_log时，LangGraph会自动合并
    execution_log: Annotated[List[dict], operator.add] = field(default_factory=list)

    # 注意：已移除error字段（单字符串），改用errors列表（支持并发写入）
