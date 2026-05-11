#!/usr/bin/env python3
"""
数据库Mock数据脚本 —— 在审改发结束后运行。

读取选题库中"已发布"状态的选题，为其生成模拟平台数据，
写入"数据库"表。

用法:
    python scripts/mock_analytics_data.py
"""

import sys
import os
import json
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.id_generator import IDGenerator
from core.utils.feishu_base import FeishuBaseManager


def generate_mock_platform_data(topic_title: str) -> dict:
    """为选题生成模拟平台数据。"""
    # 基于标题长度和关键词简单模拟不同表现
    base_score = random.uniform(0.5, 0.95)

    # 根据标题关键词调整分数
    boost_keywords = ['GPT', 'Claude', 'AI', '代码', '编程', '教程', '发布']
    for kw in boost_keywords:
        if kw in topic_title:
            base_score = min(0.98, base_score + 0.05)

    # 生成各平台数据
    gzh_reads = int(random.uniform(3000, 80000) * base_score)
    xhs_reads = int(random.uniform(5000, 120000) * base_score)
    dy_plays = int(random.uniform(10000, 500000) * base_score)
    bz_plays = int(random.uniform(8000, 200000) * base_score)

    return {
        "公众号_阅读量": gzh_reads,
        "公众号_点赞数": int(gzh_reads * random.uniform(0.02, 0.08)),
        "公众号_在看数": int(gzh_reads * random.uniform(0.01, 0.04)),
        "小红书_阅读量": xhs_reads,
        "小红书_点赞数": int(xhs_reads * random.uniform(0.03, 0.12)),
        "小红书_收藏数": int(xhs_reads * random.uniform(0.02, 0.08)),
        "小红书_评论数": int(xhs_reads * random.uniform(0.005, 0.03)),
        "抖音_播放量": dy_plays,
        "抖音_点赞数": int(dy_plays * random.uniform(0.03, 0.15)),
        "抖音_评论数": int(dy_plays * random.uniform(0.005, 0.02)),
        "B站_播放量": bz_plays,
        "B站_点赞数": int(bz_plays * random.uniform(0.02, 0.10)),
        "B站_投币数": int(bz_plays * random.uniform(0.005, 0.03)),
        "综合评分": round(base_score, 2),
        "爆点验证": "验证成功" if base_score >= 0.7 else ("部分验证" if base_score >= 0.5 else "未爆"),
    }


def run():
    print("=== Mock Analytics Data ===")
    storage = FeishuStorage()

    # 读取已发布的选题
    try:
        all_topics = storage.query("选题库", limit=100)
        published = [t for t in all_topics if t.data.get("状态") == "已发布"]
        print(f"找到 {len(published)} 条已发布选题")
    except Exception as e:
        print(f"读取选题库失败: {e}")
        return

    if not published:
        print("没有已发布选题，无需生成mock数据")
        return

    for topic_record in published:
        topic_data = topic_record.data
        topic_id = topic_data.get("id", "")
        topic_title = topic_data.get("选题标题", "")

        # 检查是否已有数据回流ID
        if topic_data.get("数据回流ID"):
            print(f"  跳过（已有数据）: {topic_title[:30]}...")
            continue

        # 生成mock数据
        mock_data = generate_mock_platform_data(topic_title)
        business_id = IDGenerator.generate("DATA")
        now_ms = FeishuBaseManager.convert_datetime_to_timestamp(datetime.now())

        record = {
            "id": business_id,
            "选题ID": topic_id,
            "选题标题": topic_title,
            **mock_data,
            "数据采集时间": now_ms,
            "数据状态": "初次采集",
        }

        try:
            storage.create("数据库", record)
            # 更新选题库的数据回流ID
            storage.update("选题库", topic_id, {"数据回流ID": business_id})
            print(f"  写入数据库: {topic_title[:30]}... 评分:{mock_data['综合评分']}")
        except Exception as e:
            print(f"  写入失败: {e}")

    print(f"\n=== 完成: 为 {len(published)} 条选题生成mock数据 ===")


if __name__ == "__main__":
    run()
