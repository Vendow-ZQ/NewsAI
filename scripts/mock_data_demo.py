#!/usr/bin/env python3
"""演示脚本：从内容资产库取最新分发记录，用 LLM 生成模拟数据写入数据库。

此脚本不是 MultiAgent 系统的一部分，仅用于演示效果。
运行方式: python scripts/mock_data_demo.py
"""

import sys
import json
import os

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.id_generator import IDGenerator
from core.agents.base import current_timestamp_ms
from core.utils.llm_output_parser import invoke_with_retry


def main():
    print("=" * 60)
    print("Mock Data Demo: 生成分发数据到 数据库 表")
    print("=" * 60)

    storage = FeishuStorage()
    llm = get_llm()

    # 1. 取最新一条已分发的内容资产
    assets = storage.query("内容资产库", limit=10)
    asset = None
    for a in assets:
        if a.data.get("分发状态") in ["已生成", "已完成"]:
            asset = a.data
            break

    if not asset:
        print("没有找到已分发的内容资产")
        return

    asset_id = asset.get("id")
    topic_id = asset.get("选题ID")
    topic_title = asset.get("选题标题", "")
    print(f"选中资产: {asset_id}")
    print(f"选题: {topic_title}")

    # 2. 用 LLM 生成模拟数据
    prompt = f"""你是数据生成器。根据以下选题信息，生成一套合理的多平台分发模拟数据。

选题标题: {topic_title}

请输出 JSON 格式:
{{
  "公众号_阅读量": 数字,
  "公众号_点赞数": 数字,
  "公众号_在看数": 数字,
  "小红书_阅读量": 数字,
  "小红书_点赞数": 数字,
  "小红书_收藏数": 数字,
  "小红书_评论数": 数字,
  "抖音_播放量": 数字,
  "抖音_点赞数": 数字,
  "抖音_评论数": 数字,
  "视频号_播放量": 数字,
  "视频号_点赞数": 数字,
  "视频号_转发数": 数字,
  "B站_播放量": 数字,
  "B站_点赞数": 数字,
  "B站_投币数": 数字,
  "综合评分": 0-1 之间的小数,
  "爆点验证": "验证成功" 或 "部分验证" 或 "未爆"
}}

要求：数据要合理，有高低差异，不要所有平台都一样。"""

    messages = [
        {"role": "system", "content": "你专门生成合理的社交媒体模拟数据。只输出 JSON，不要其他文字。"},
        {"role": "user", "content": prompt},
    ]

    thinking, answer, raw = invoke_with_retry(llm, messages, max_retries=3)

    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except:
            print(f"LLM 返回格式错误: {answer}")
            return

    # 3. 写入数据库表
    data_id = IDGenerator.generate("DATA")
    record = {
        "id": data_id,
        "选题ID": topic_id,
        "选题标题": topic_title,
        "公众号_阅读量": answer.get("公众号_阅读量", 0),
        "公众号_点赞数": answer.get("公众号_点赞数", 0),
        "公众号_在看数": answer.get("公众号_在看数", 0),
        "小红书_阅读量": answer.get("小红书_阅读量", 0),
        "小红书_点赞数": answer.get("小红书_点赞数", 0),
        "小红书_收藏数": answer.get("小红书_收藏数", 0),
        "小红书_评论数": answer.get("小红书_评论数", 0),
        "抖音_播放量": answer.get("抖音_播放量", 0),
        "抖音_点赞数": answer.get("抖音_点赞数", 0),
        "抖音_评论数": answer.get("抖音_评论数", 0),
        "视频号_播放量": answer.get("视频号_播放量", 0),
        "视频号_点赞数": answer.get("视频号_点赞数", 0),
        "视频号_转发数": answer.get("视频号_转发数", 0),
        "B站_播放量": answer.get("B站_播放量", 0),
        "B站_点赞数": answer.get("B站_点赞数", 0),
        "B站_投币数": answer.get("B站_投币数", 0),
        "综合评分": answer.get("综合评分", 0.5),
        "爆点验证": answer.get("爆点验证", "未爆"),
        "数据采集时间": current_timestamp_ms(),
        "数据状态": "待分析",
    }

    try:
        storage.create("数据库", record)
        print(f"写入数据库: {data_id}")
    except Exception as e:
        print(f"写入失败: {e}")
        return

    # 4. 更新选题库的数据回流ID
    if topic_id:
        try:
            storage.update("选题库", topic_id, {"数据回流ID": data_id})
            print(f"更新选题库回流ID: {data_id}")
        except Exception as e:
            print(f"更新选题库失败: {e}")

    print("=" * 60)
    print(f"完成！DATA ID: {data_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
