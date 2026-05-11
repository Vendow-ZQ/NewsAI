"""LangGraph 共享 State 定义 - v3.0。

支持 6 状态字段的状态机：
- current_topic_id: 当前选题 ID
- current_asset_id: 当前资产 ID（v3 新增）
- revision_count: 审改轮次（0-3）
- max_revisions: 最大审改轮次（默认 3）
- review_verdict: 审查结论（"通过" / "需修改"）
- errors: 错误列表（并发安全）
- execution_log: 执行日志（并发安全）
"""

from dataclasses import dataclass, field
from typing import Optional, List, Annotated
import operator


@dataclass
class NewsAIState:
    """NewsAI LangGraph 状态类。

    用于在 Agent 节点之间传递状态信息。
    支持并发写入 execution_log 和 errors（通过 Annotated 合并）。
    """
    current_topic_id: Optional[str] = None
    current_asset_id: Optional[str] = None  # v3 新增：关联资产 ID
    koc_id: Optional[str] = "KOC-001"
    revision_count: int = 0
    max_revisions: int = 3
    review_verdict: Optional[str] = None  # "通过" / "需修改"

    # 使用 Annotated 支持并发节点写入错误信息
    errors: Annotated[List[str], operator.add] = field(default_factory=list)

    # execution_log 使用 Annotated + operator.add 实现并发合并
    execution_log: Annotated[List[dict], operator.add] = field(default_factory=list)
