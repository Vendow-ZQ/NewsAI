"""
NewsAI Bootstrap Script
一键复现：建表 + 种子数据 + 跑一轮 demo
"""

import asyncio
import sys

from dotenv import load_dotenv
from loguru import logger


def check_env():
    """检查必要的环境变量是否已配置。"""
    import os

    required = ["LLM_API_KEY", "LLM_MODEL", "LARK_APP_ID", "LARK_APP_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        logger.error(f"缺少环境变量: {', '.join(missing)}")
        logger.info("请复制 .env.example 为 .env 并填入对应值")
        sys.exit(1)


async def bootstrap():
    """一键启动流程。"""
    load_dotenv()
    check_env()

    logger.info("=== NewsAI Bootstrap ===")

    # Step 1: 创建多维表格（如不存在）
    logger.info("[1/4] 创建飞书多维表格...")
    # TODO: feishu_adapter.bootstrap

    # Step 2: 批量建表
    logger.info("[2/4] 批量建表...")
    # TODO: feishu_adapter.schemas

    # Step 3: 写入种子数据
    logger.info("[3/4] 写入种子数据...")
    # TODO: seed data

    # Step 4: 跑一轮 demo
    logger.info("[4/4] 运行一轮 LangGraph 流程...")
    # TODO: run graph

    logger.info("=== Bootstrap 完成 ===")


if __name__ == "__main__":
    asyncio.run(bootstrap())
