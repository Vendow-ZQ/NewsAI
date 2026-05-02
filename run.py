"""
NewsAI 主入口
启动 LangGraph 跑一轮完整的新闻编辑流程。

用法:
    python run.py --once              # 跑一轮
    python run.py --agent topic       # 单独跑某个 Agent
"""

import argparse
import asyncio

from dotenv import load_dotenv
from loguru import logger


def parse_args():
    parser = argparse.ArgumentParser(description="NewsAI Runner")
    parser.add_argument("--once", action="store_true", help="跑一轮完整流程")
    parser.add_argument("--agent", type=str, default=None, help="单独跑某个 Agent（调试用）")
    return parser.parse_args()


async def run_once():
    """执行一轮完整的新闻编辑流程。"""
    logger.info("开始一轮完整流程...")
    # TODO: build_graph() -> invoke
    logger.info("流程完成")


async def run_agent(agent_name: str):
    """单独运行指定 Agent（调试用）。"""
    logger.info(f"单独运行 Agent: {agent_name}")
    # TODO: instantiate and run single agent
    logger.info(f"Agent {agent_name} 运行完成")


async def main():
    load_dotenv()
    args = parse_args()

    if args.agent:
        await run_agent(args.agent)
    else:
        await run_once()


if __name__ == "__main__":
    asyncio.run(main())
