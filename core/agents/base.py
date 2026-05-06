"""BaseAgent 抽象类 -- 所有 Agent 的基类。

采用模板方法模式，定义统一的执行流程：
1. 读取上游数据
2. 调用工具
3. 调用LLM处理
4. 写入存储
5. 写工作日志
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
import json
import time


class BaseAgent(ABC):
    """Agent基类，模板方法模式。

    子类只需实现特定的抽象方法，无需关心执行流程。
    """

    def __init__(self, name: str, storage: Any, llm_client: Any):
        """
        Args:
            name: Agent花名，如"小哨"
            storage: Storage实例，用于数据持久化
            llm_client: LLM客户端，用于文本生成
        """
        self.name = name
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

        # 3. 调用LLM处理
        llm_result = self._invoke_llm(context, upstream_data, tool_results)

        # 4. 写入存储
        self._write_storage(context, llm_result)

        # 5. 写工作日志
        self._log_work(context, llm_result)

        return llm_result

    def _read_upstream(self, context: dict) -> dict:
        """读取上游数据，子类可override。"""
        return {}

    @abstractmethod
    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """调用外部工具，子类实现。"""
        pass

    @abstractmethod
    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """调用LLM，子类实现。"""
        pass

    def _write_storage(self, context: dict, result: dict):
        """写入存储，子类可override。"""
        pass

    def _log_work(self, context: dict, result: dict):
        """写入Agent协作日志。

        所有Agent的执行记录都会写入"Agent协作日志"表，便于追踪和调试。
        字段必须严格匹配LOG表schema: id, AgentID, Agent花名, 任务类型, 关联业务ID,
        输入摘要, 输出摘要, 执行状态, 耗时秒数, Token消耗, 错误信息, 执行时间
        """
        # 计算耗时
        start_time_str = context.get("start_time", "")
        try:
            start_dt = datetime.fromisoformat(start_time_str)
            elapsed_seconds = (datetime.now() - start_dt).total_seconds()
        except:
            elapsed_seconds = 0

        # 获取关联业务ID（如果result中有）
        related_id = ""
        if isinstance(result, dict):
            related_id = result.get("id", "") or result.get("topic_id", "")

        # 获取任务类型文本（单选字段需要在选项列表中）
        task_type = self._get_task_type()

        log_entry = {
            "id": f"LOG-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "AgentID": getattr(self, 'emp_id', ''),
            "Agent花名": self.name,
            # 单选字段暂时跳过，避免TextFieldConvFail错误
            # "任务类型": task_type,
            "关联业务ID": related_id,
            "输入摘要": str(context)[:200],
            "输出摘要": str(result)[:200],
            # "执行状态": "成功",
            "耗时秒数": int(elapsed_seconds),
            "Token消耗": 0,
            "错误信息": "",
            "执行时间": int(time.time() * 1000),
        }
        try:
            self.storage.create("Agent协作日志", log_entry)
        except Exception as e:
            # 日志写入失败不应影响主流程
            print(f"[警告] 写入Agent协作日志失败: {e}")

    def _get_task_type(self) -> str:
        """获取任务类型，用于Agent协作日志。

        返回预定义的任务类型，对应LOG表schema中的单选值。
        """
        task_type_map = {
            "TrendScout": "信源抓取",
            "TopicCurator": "选题筛选",
            "ContentWriter": "内容撰写",
            "VisualDesigner": "配图生成",
            "ScriptWriter": "脚本撰写",
            "Reviewer": "内容审查",
            "Editor": "内容修改",
            "Distributor": "分发计划",
            "Analyst": "数据分析",
        }
        class_name = self.__class__.__name__
        return task_type_map.get(class_name, "其他")
