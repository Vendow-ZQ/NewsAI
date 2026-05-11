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
    将mock数据转换为飞书Base字段格式

    处理字段映射和数据转换：
    - 信源配置: mock格式 -> tables.py定义格式
    - Agent花名册: mock格式 -> tables.py定义格式
    - 热帖库: mock格式 -> tables.py定义格式

    注意: 飞书Base日期时间字段需要毫秒级时间戳(整数)
    """
    transformed = []
    now_ts = int(datetime.now().timestamp() * 1000)

    for item in raw_data:
        try:
            if table_name == "信源配置":
                # 从 mock_data/src_sources.json 转换
                record = {
                    "id": item.get("id", ""),
                    "信源名称": item.get("信源名称", ""),
                    "平台": item.get("信源名称", "").split()[0] if " " in item.get("信源名称", "") else item.get("信源名称", ""),
                    "类型": "Mock数据" if "MOCK" in item.get("id", "") else "真实爬虫",
                    "配置JSON": json.dumps(item.get("采集规则", {}), ensure_ascii=False),
                    "每次抓取上限": 5 if "MOCK" not in item.get("id", "") else 10,
                    "是否启用": item.get("采集状态") == "活跃" or item.get("采集状态") == "Mock",
                    "优先级": int(item.get("权重", 0.5) * 10),
                    "创建时间": now_ts,
                }
                transformed.append(record)

            elif table_name == "Agent花名册":
                # 从 mock_data/agent_roster.json 转换
                record = {
                    "id": item.get("id", "").replace("AGENT-", "EMP-"),
                    "花名": item.get("Agent名称", ""),
                    "英文代号": item.get("Agent编码", ""),
                    "部门": item.get("所属部门", ""),
                    "职责描述": item.get("职责描述", ""),
                    "输入": item.get("输入", ""),
                    "输出": item.get("输出", ""),
                    "调用模型": item.get("LLM模型", ""),
                    "系统提示词": "",  # mock数据中没有
                    "是否启用": item.get("状态") == "活跃",
                    "创建时间": now_ts,
                }
                transformed.append(record)

            elif table_name == "热帖库":
                # 从 mock_data/trend_hotposts.json 转换
                hot_metrics = item.get("热度指标", {})
                engagement = 0
                if "评论数" in hot_metrics:
                    engagement += hot_metrics["评论数"]
                if "点赞数" in hot_metrics:
                    engagement += hot_metrics["点赞数"]
                if "转发数" in hot_metrics:
                    engagement += hot_metrics["转发数"]

                # 解析发布时间
                pub_time = item.get("发布时间", "")
                try:
                    pub_ts = to_feishu_datetime(pub_time) if pub_time else now_ts
                except Exception:
                    pub_ts = now_ts

                # 解析采集时间
                crawl_time = item.get("采集时间", "")
                try:
                    crawl_ts = to_feishu_datetime(crawl_time) if crawl_time else now_ts
                except Exception:
                    crawl_ts = now_ts

                record = {
                    "id": item.get("id", ""),
                    "信源ID": item.get("信源 ID", ""),
                    "信源平台": item.get("信源名称", ""),
                    "标题": item.get("热帖标题", ""),
                    "原文链接": {"text": "查看原文", "link": item.get("原始链接", "")} if item.get("原始链接") else None,
                    "原文摘要": item.get("内容摘要", ""),
                    "原文语言": "英文" if item.get("信源名称") in ["arXiv", "HackerNews", "GitHub", "Reddit r/LocalLLaMA", "Reddit r/MachineLearning", "X/Twitter"] else "中文",
                    "主题标签": item.get("关键词", []),
                    "阅览量": hot_metrics.get("阅读数", hot_metrics.get("播放量", 0)),
                    "互动量": engagement,
                    "发布时间": pub_ts,
                    "抓取时间": crawl_ts,
                    "热度评分": 0.7,  # 默认值
                    "内容质量": "中",  # 默认值
                    "状态": "待选" if item.get("处理状态") == "待分析" else "已选",
                }
                transformed.append(record)

            elif table_name == "KOC人设":
                # 使用 tables.py 中定义的种子数据，但需要转换日期时间
                record = dict(item)
                # 转换创建时间为时间戳
                if "创建时间" in record:
                    try:
                        record["创建时间"] = to_feishu_datetime(record["创建时间"])
                    except Exception:
                        record["创建时间"] = now_ts
                transformed.append(record)

            else:
                # 其他表直接使用原始数据
                transformed.append(item)

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

    # 定义种子数据源
    seed_configs = [
        ("信源配置", "src_sources.json", None),  # 从mock_data加载并转换
        ("Agent花名册", "agent_roster.json", None),  # 从mock_data加载并转换
        ("热帖库", "trend_hotposts.json", None),  # 可选，用于demo
        ("KOC人设", None, "KOC人设"),  # 从tables.py内置数据加载
    ]

    for table_name, mock_file, table_key in seed_configs:
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

            # 获取种子数据
            if mock_file:
                raw_data = load_mock_data(mock_file)
                seed_data = transform_seed_data(table_name, raw_data)
            elif table_key:
                raw_data = get_seed_data(table_key)
                seed_data = transform_seed_data(table_name, raw_data)
            else:
                continue

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
