"""BaseAgent 抽象类 -- 所有 Agent 的基类。

v3.0 模板方法模式：
1. 读取上游数据（含 KOC 人设）
2. 调用工具
3. 调用 LLM 处理（带重试）
4. 写入存储
5. 写工作日志

关键改进：
- 所有 Agent 必须从 KOC 人设表读取 KOC
- LLM 调用统一使用 invoke_with_retry
- 输出解析统一使用 parse_thinking_answer
"""

from abc import ABC, abstractmethod
from datetime import datetime
import json
import time
from typing import Any


class BaseAgent(ABC):
    """Agent 基类，模板方法模式。

    子类只需实现特定的抽象方法，无需关心执行流程。
    """

    name: str = "Agent"
    english_name: str = "Agent"
    emoji: str = "🤖"

    def __init__(self, storage: Any, llm_client: Any):
        """
        Args:
            storage: Storage 实例，用于数据持久化
            llm_client: LLM 客户端，用于文本生成
        """
        self.storage = storage
        self.llm = llm_client

    def execute(self, context: dict) -> dict:
        """
        模板方法：执行完整流程。

        Args:
            context: 执行上下文，包含任务参数

        Returns:
            执行结果字典
        """
        start_time = datetime.now().isoformat()
        context["start_time"] = start_time

        # 1. 读取上游数据
        upstream_data = self._read_upstream(context)

        # 2. 调用工具（如需要）
        tool_results = self._invoke_tools(context, upstream_data)

        # 3. 调用 LLM 处理
        llm_result = self._invoke_llm(context, upstream_data, tool_results)

        # 4. 写入存储
        self._write_storage(context, llm_result)

        # 5. 写工作日志
        self._log_work(context, llm_result)

        return llm_result

    def _read_upstream(self, context: dict) -> dict:
        """读取上游数据，子类可 override。"""
        return {}

    @abstractmethod
    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """调用外部工具，子类实现。"""
        pass

    @abstractmethod
    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """调用 LLM，子类实现。"""
        pass

    def _write_storage(self, context: dict, result: dict):
        """写入存储，子类可 override。"""
        pass

    def _log_work(self, context: dict, result: dict):
        """写入 Agent 协作日志。"""
        # 解析开始时间
        start_time_str = context.get("start_time", "")
        start_ts = current_timestamp_ms()
        try:
            start_dt = datetime.fromisoformat(start_time_str)
            start_ts = int(start_dt.timestamp() * 1000)
            elapsed_seconds = (datetime.now() - start_dt).total_seconds()
        except Exception:
            elapsed_seconds = 0

        end_ts = current_timestamp_ms()

        related_id = ""
        if isinstance(result, dict):
            related_id = result.get("id", "") or result.get("topic_id", "") or result.get("asset_id", "")

        task_type = self._get_task_type()

        output_summary = ""
        if isinstance(result, dict):
            if "count" in result:
                output_summary = f"产出 {result['count']} 条结果"
            elif "items" in result and isinstance(result["items"], list):
                output_summary = f"处理 {len(result['items'])} 条数据"
            elif "topics" in result and isinstance(result["topics"], list):
                output_summary = f"生成 {len(result['topics'])} 条选题"
            elif "contents" in result and isinstance(result["contents"], list):
                output_summary = f"撰写 {len(result['contents'])} 条内容"
            elif "candidates" in result and isinstance(result["candidates"], list):
                output_summary = f"筛选 {len(result['candidates'])} 条候选"
            elif "verdict" in result:
                output_summary = f"审查结果: {result['verdict']}"
            elif "log_summary" in result:
                output_summary = result["log_summary"]
            else:
                output_summary = f"完成: {list(result.keys())}"
        else:
            output_summary = "Completed"

        log_entry = {
            "id": f"LOG-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.name}",
            "AgentID": self._get_agent_id(),
            "Agent花名": str(self.name),
            "任务类型": task_type,
            "关联业务ID": related_id if related_id else "",
            "输入摘要": f"{self.name} 执行 {task_type} 任务",
            "输出摘要": output_summary,
            "执行状态": "成功",
            "开始时间": start_ts,
            "结束时间": end_ts,
            "耗时秒数": round(elapsed_seconds, 1),
        }
        try:
            self.storage.create("Agent协作日志", log_entry)
            print(f"[日志] {self.name}: 成功写入Agent协作日志")
        except Exception as e:
            print(f"[警告] {self.name}: 写入Agent协作日志失败: {e}")

    def _get_agent_id(self) -> str:
        """获取 Agent 业务 ID，匹配 Agent 花名册。"""
        agent_id_map = {
            "TrendScoutAgent": "EMP-001",
            "TopicCuratorAgent": "EMP-002",
            "ContentWriterAgent": "EMP-003",
            "VisualDesignerAgent": "EMP-004",
            "ScriptWriterAgent": "EMP-005",
            "ReviewerAgent": "EMP-006",
            "EditorAgent": "EMP-007",
            "DistributorAgent": "EMP-008",
            "AnalystAgent": "EMP-009",
        }
        return agent_id_map.get(self.__class__.__name__, f"EMP-{self.name}")

    def _get_task_type(self) -> str:
        """获取任务类型，用于 Agent 协作日志。"""
        task_type_map = {
            "TrendScout": "爬取热点",
            "TopicCurator": "选题",
            "ContentWriter": "写作",
            "VisualDesigner": "写Prompt",
            "ScriptWriter": "写脚本",
            "Reviewer": "审查",
            "Editor": "修改",
            "Distributor": "分发",
            "Analyst": "数据分析",
        }
        class_name = self.__class__.__name__
        return task_type_map.get(class_name, "其他")


def parse_koc_data(raw_koc: dict) -> dict:
    """解析 KOC 人设数据。v3.0: 表已使用扁平字段，无需 JSON 展开。"""
    if not raw_koc:
        return {}
    result = dict(raw_koc)
    # 兼容旧表：如果扁平字段缺失，从旧 JSON 字段和 fallback 推导
    if "账号名" not in result:
        result["账号名"] = raw_koc.get("人设名称", "")
    if "一句话定位" not in result:
        result["一句话定位"] = raw_koc.get("人设简介", "")
    for field in ["基础设定JSON", "语言风格JSON", "内容偏好JSON", "平台策略JSON"]:
        val = raw_koc.get(field, "")
        if val and isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    for sub_key, sub_val in parsed.items():
                        if sub_key not in result:
                            result[sub_key] = sub_val
            except json.JSONDecodeError:
                pass
    return result


def current_timestamp_ms() -> int:
    """当前时间戳（毫秒）"""
    return int(datetime.now().timestamp() * 1000)


def today_str() -> str:
    """今天日期字符串 YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")
