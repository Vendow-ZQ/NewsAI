"""Agent模块 - 9位虚拟员工。

v2 架构（2026-05-04）：
- 信息组：小哨 TrendScout (EMP-001)
- 决策组：小编 TopicCurator (EMP-002)
- 生产组：小文 ContentWriter (EMP-003)、小图 VisualDesigner (EMP-004)、小播 ScriptWriter (EMP-005)
- 治理组：小审 Reviewer (EMP-006)、小改 Editor (EMP-007)、小发 Distributor (EMP-008)
- 复盘：小数 Analyst (EMP-009)
"""

from core.agents.base import BaseAgent
from core.agents.trend_scout import TrendScoutAgent, TrendScout
from core.agents.topic_curator import TopicCuratorAgent, TopicCurator
from core.agents.content_writer import ContentWriterAgent, ContentWriter
from core.agents.visual_designer import VisualDesignerAgent, VisualDesigner
from core.agents.script_writer import ScriptWriterAgent, ScriptWriter
from core.agents.reviewer import ReviewerAgent, Reviewer
from core.agents.editor import EditorAgent, Editor
from core.agents.distributor import DistributorAgent, Distributor
from core.agents.analyst import AnalystAgent, Analyst

__all__ = [
    "BaseAgent",
    # 信息组
    "TrendScoutAgent", "TrendScout",
    # 决策组
    "TopicCuratorAgent", "TopicCurator",
    # 生产组
    "ContentWriterAgent", "ContentWriter",
    "VisualDesignerAgent", "VisualDesigner",
    "ScriptWriterAgent", "ScriptWriter",
    # 治理组
    "ReviewerAgent", "Reviewer",
    "EditorAgent", "Editor",  # EMP-007
    "DistributorAgent", "Distributor",
    # 复盘
    "AnalystAgent", "Analyst",
]
