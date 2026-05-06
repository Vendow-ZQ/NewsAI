"""清理旧表并重新 bootstrap（用于字段变更后重建表结构）。"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from core.utils.feishu_base import FeishuBaseManager


async def main():
    base = FeishuBaseManager()
    tables = base.list_tables()

    target_tables = [
        "信源配置", "热帖库", "选题库", "数据库",
        "KOC人设", "Agent花名册", "Agent协作日志"
    ]

    for name in target_tables:
        if name in tables:
            logger.info(f"删除旧表: {name}")
            try:
                base.delete_table(tables[name])
                logger.info(f"  已删除")
            except Exception as e:
                logger.warning(f"  删除失败: {e}")
        else:
            logger.info(f"表不存在，跳过: {name}")

    # 清空 ID 映射缓存
    mapping_file = ".id_mapping.json"
    if os.path.exists(mapping_file):
        os.remove(mapping_file)
        logger.info(f"已删除缓存: {mapping_file}")

    logger.info("清理完成，现在运行 bootstrap.py...")

    # 调用 bootstrap
    from bootstrap import bootstrap
    await bootstrap()


if __name__ == "__main__":
    asyncio.run(main())
