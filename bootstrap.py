"""
NewsAI Bootstrap Script
一键复现：建表 + 种子数据

使用方法:
    python bootstrap.py

环境要求:
    - .env 文件中配置 LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN
    - 可选: LARK_BASE_APP_TOKEN 如未设置，会提示用户创建Base并配置
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils.feishu_base import FeishuBaseManager
from feishu_adapter.base.tables import (
    get_table_fields,
    get_seed_data,
)


def check_env():
    """检查必要的环境变量是否已配置。"""
    required = ["LARK_APP_ID", "LARK_APP_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        logger.error(f"缺少环境变量: {', '.join(missing)}")
        logger.info("请复制 .env.example 为 .env 并填入对应值")
        sys.exit(1)

    # 检查 Base Token
    base_token = os.getenv("LARK_BASE_APP_TOKEN")
    if not base_token:
        logger.warning("未设置 LARK_BASE_APP_TOKEN 环境变量")
        logger.info("""
请按以下步骤操作：
1. 在飞书创建一个多维表格(Base)
2. 从URL中复制 Base Token (格式如: XXXXXXXXXXXXXXXX)
3. 在 .env 文件中添加: LARK_BASE_APP_TOKEN=你的BaseToken
4. 将飞书应用添加为该Base的协作者
        """)
        return False
    return True


def load_mock_data(filename: str) -> List[Dict[str, Any]]:
    """从mock_data目录加载JSON数据"""
    filepath = os.path.join(os.path.dirname(__file__), "mock_data", filename)
    if not os.path.exists(filepath):
        logger.warning(f"Mock数据文件不存在: {filepath}")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"  加载 {filename}: {len(data)} 条记录")
            return data
    except Exception as e:
        logger.error(f"  加载 {filename} 失败: {e}")
        return []


def to_feishu_datetime(iso_string: str) -> int:
    """将ISO格式时间字符串转换为飞书Base要求的毫秒时间戳"""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except:
        return int(datetime.now().timestamp() * 1000)


def transform_seed_data(table_name: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 tables.py 中的种子数据转换为飞书Base字段格式。

    只做通用转换：
    - 日期时间字符串 -> 毫秒时间戳
    - 确保布尔值正确

    字段映射已在 tables.py 的 *_SEED_DATA 中完成，此处不再转换。
    """
    transformed = []
    now_ts = int(datetime.now().timestamp() * 1000)

    for item in raw_data:
        try:
            record = dict(item)

            # 转换日期时间字段
            for time_field in ["创建时间", "更新时间", "发布时间", "抓取时间", "选定时间"]:
                if time_field in record and isinstance(record[time_field], str):
                    try:
                        record[time_field] = to_feishu_datetime(record[time_field])
                    except Exception:
                        record[time_field] = now_ts

            # 确保布尔值正确（YAML解析可能返回字符串"true"）
            for bool_field in ["是否启用", "是否默认"]:
                if bool_field in record:
                    val = record[bool_field]
                    if isinstance(val, str):
                        record[bool_field] = val.lower() in ("true", "yes", "1", "是")

            transformed.append(record)

        except Exception as e:
            logger.warning(f"  转换记录失败: {e}")
            continue

    return transformed


async def setup_tables(base: FeishuBaseManager) -> Dict[str, str]:
    """
    Step 2: 批量建表（7张表）

    Returns:
        {表名: table_id} 映射
    """
    logger.info("[2/4] 批量建表...")

    # 获取现有表
    try:
        existing_tables = base.list_tables()
        logger.info(f"  现有表: {list(existing_tables.keys())}")
    except Exception as e:
        logger.error(f"  获取现有表失败: {e}")
        existing_tables = {}

    table_ids = {}

    # 按顺序创建8张表（v3.0：新增内容资产库）
    table_order = [
        "信源配置",
        "热帖库",
        "选题库",
        "内容资产库",  # v3.0 新增
        "数据库",
        "KOC人设",
        "Agent花名册",
        "Agent协作日志",
    ]

    for table_name in table_order:
        try:
            # 检查表是否已存在
            if table_name in existing_tables:
                logger.info(f"  表已存在: {table_name} ({existing_tables[table_name]})")
                table_ids[table_name] = existing_tables[table_name]

                # 确保所有字段存在
                fields = get_table_fields(table_name)
                base.ensure_fields(existing_tables[table_name], fields)
                continue

            # 创建新表
            fields = get_table_fields(table_name)
            table_id = base.create_table(table_name, fields)
            table_ids[table_name] = table_id
            logger.info(f"  创建表成功: {table_name} ({table_id})")

            # 确保所有字段存在（创建后可能缺少某些字段）
            base.ensure_fields(table_id, fields)

        except Exception as e:
            logger.error(f"  创建表失败 [{table_name}]: {e}")
            raise

    logger.info(f"  共处理 {len(table_ids)} 张表")
    return table_ids


async def seed_data(base: FeishuBaseManager, table_ids: Dict[str, str]):
    """
    Step 3: 写入种子数据
    """
    logger.info("[3/4] 写入种子数据...")

    # 定义种子数据源：全部从 tables.py 硬编码加载，统一维护
    seed_configs = [
        ("信源配置", "信源配置"),
        ("Agent花名册", "Agent花名册"),
        ("KOC人设", "KOC人设"),
    ]

    for table_name, table_key in seed_configs:
        if table_name not in table_ids:
            logger.warning(f"  表不存在，跳过: {table_name}")
            continue

        table_id = table_ids[table_name]

        try:
            # 检查是否已有数据（幂等性）
            existing_records = base.list_records(table_id)
            if existing_records:
                logger.info(f"  [{table_name}] 已有 {len(existing_records)} 条记录，跳过")
                continue

            # 从 tables.py 获取种子数据并转换时间戳
            raw_data = get_seed_data(table_key)
            seed_data = transform_seed_data(table_name, raw_data)

            if not seed_data:
                logger.info(f"  [{table_name}] 无种子数据")
                continue

            # 批量创建记录
            records = [{"fields": record} for record in seed_data]
            record_ids = base.batch_create_records(table_id, records)
            logger.info(f"  [{table_name}] 写入 {len(record_ids)} 条记录")

        except Exception as e:
            logger.error(f"  写入种子数据失败 [{table_name}]: {e}")
            import traceback
            traceback.print_exc()
            # 不中断，继续处理其他表


async def print_summary(base: FeishuBaseManager, table_ids: Dict[str, str]):
    """
    Step 4: 打印结果摘要
    """
    logger.info("[4/4] 生成结果摘要...")

    base_token = os.getenv("LARK_BASE_APP_TOKEN", "")
    base_url = f"https://base.feishu.cn/{base_token}" if base_token else "未配置"

    print("\n" + "=" * 60)
    print("NewsAI Bootstrap 完成!")
    print("=" * 60)

    print(f"\n[Base] 访问链接: {base_url}")

    print("\n[表记录统计]")
    print("-" * 40)

    total_records = 0
    for table_name, table_id in table_ids.items():
        try:
            records = base.list_records(table_id)
            count = len(records)
            total_records += count
            print(f"  {table_name:12s}: {count:4d} 条记录")
        except Exception as e:
            print(f"  {table_name:12s}: 获取失败 ({e})")

    print("-" * 40)
    print(f"  {'总计':12s}: {total_records:4d} 条记录")

    print("\n[下一步操作]:")
    print("  1. 访问飞书Base查看创建的表和数据")
    print("  2. 运行 'python tests/test_trend_scout_e2e.py' 测试小哨Agent")
    print("  3. 运行 'python -m core.agents.trend_scout' 启动信息采集")

    print("\n" + "=" * 60)


async def bootstrap():
    """一键启动流程。"""
    logger.info("=== NewsAI Bootstrap ===")

    # Step 0: 检查环境
    logger.info("[0/4] 检查环境配置...")
    has_base = check_env()
    if not has_base:
        logger.error("请先配置 LARK_BASE_APP_TOKEN 后再运行")
        sys.exit(1)

    # 初始化 FeishuBaseManager
    try:
        base = FeishuBaseManager()
        logger.info("  FeishuBaseManager 初始化成功")
    except Exception as e:
        logger.error(f"  初始化失败: {e}")
        sys.exit(1)

    # Step 1: 验证Base连接
    logger.info("[1/4] 验证飞书Base连接...")
    try:
        tables = base.list_tables()
        logger.info(f"  连接成功! 现有 {len(tables)} 张表")
    except Exception as e:
        logger.error(f"  连接失败: {e}")
        logger.error("  请检查:")
        logger.error("    1. LARK_APP_ID 和 LARK_APP_SECRET 是否正确")
        logger.error("    2. LARK_BASE_APP_TOKEN 是否正确")
        logger.error("    3. 飞书应用是否已添加为该Base的协作者")
        sys.exit(1)

    # Step 2: 批量建表
    table_ids = await setup_tables(base)

    # Step 3: 写入种子数据
    await seed_data(base, table_ids)

    # Step 4: 打印结果
    await print_summary(base, table_ids)

    logger.info("=== Bootstrap 完成 ===")


if __name__ == "__main__":
    asyncio.run(bootstrap())
