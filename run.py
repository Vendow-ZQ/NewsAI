#!/usr/bin/env python3
"""
NewsAI 主入口
启动 LangGraph 跑一轮完整的新闻编辑流程。

用法:
    python run.py --once              # 跑一轮完整流程
    python run.py --once --topic TOPIC_ID  # 指定选题ID运行
    python run.py --agent topic       # 单独跑某个 Agent（调试用）
"""

import argparse
import asyncio

from dotenv import load_dotenv
from loguru import logger


async def run_once(topic_id: str = None):
    """执行一轮完整的新闻编辑流程。"""
    logger.info("开始一轮完整流程...")

    try:
        # 延迟导入，避免在模块级别初始化失败
        from core.graph.builder import build_newsai_graph
        from core.graph.state import NewsAIState
        from feishu_adapter.feishu_storage import FeishuStorage
        from core.llm.client import get_llm

        # 初始化存储和LLM
        storage = FeishuStorage()
        llm = get_llm()

        # 构建图
        graph = build_newsai_graph(storage, llm)

        # 创建初始状态
        state = NewsAIState(current_topic_id=topic_id)

        # 执行图
        logger.info(f"执行图流程，选题ID: {topic_id or '未指定'}")
        result = await graph.ainvoke(state)

        logger.info("流程完成")
        logger.info(f"执行日志: {result.get('execution_log', [])}")

        return result

    except Exception as e:
        logger.error(f"流程执行失败: {e}")
        raise


async def run_agent(agent_name: str):
    """单独运行指定 Agent（调试用）。"""
    logger.info(f"单独运行 Agent: {agent_name}")

    try:
        from feishu_adapter.feishu_storage import FeishuStorage
        from core.llm.client import get_llm

        storage = FeishuStorage()
        llm = get_llm()

        # Agent映射
        agent_map = {
            "trend": ("core.agents.trend_scout", "TrendScoutAgent"),
            "topic": ("core.agents.topic_curator", "TopicCuratorAgent"),
            "content": ("core.agents.content_writer", "ContentWriterAgent"),
            "visual": ("core.agents.visual_designer", "VisualDesignerAgent"),
            "script": ("core.agents.script_writer", "ScriptWriterAgent"),
            "review": ("core.agents.reviewer", "ReviewerAgent"),
            "distribute": ("core.agents.distributor", "DistributorAgent"),
            "analyze": ("core.agents.analyst", "AnalystAgent"),
        }

        if agent_name not in agent_map:
            logger.error(f"未知的Agent: {agent_name}")
            logger.info(f"可用的Agent: {list(agent_map.keys())}")
            return

        module_path, class_name = agent_map[agent_name]
        module = __import__(module_path, fromlist=[class_name])
        agent_class = getattr(module, class_name)

        agent = agent_class(storage, llm)
        result = agent.execute({})

        logger.info(f"Agent {agent_name} 运行完成")
        logger.info(f"结果: {result}")

    except Exception as e:
        logger.error(f"Agent运行失败: {e}")
        raise


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="NewsAI Runner")
    parser.add_argument("--once", action="store_true", help="跑一轮完整流程")
    parser.add_argument("--agent", type=str, default=None, help="单独跑某个 Agent（调试用）")
    parser.add_argument("--topic", type=str, default=None, help="指定选题ID")
    args = parser.parse_args()

    if args.agent:
        await run_agent(args.agent)
    elif args.once:
        await run_once(args.topic)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
