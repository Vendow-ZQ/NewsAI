# -*- coding: utf-8 -*-
"""
单独运行小编 Agent - 从热帖库选题
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 关闭mock模式
os.environ["LLM_MOCK"] = "0"

def retry_operation(func, max_retries=5, delay=3):
    """带重试的操作"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            print(f"  [重试] 第{attempt+1}次失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise
    return None

def main():
    print("=" * 70)
    print("[小编] TopicCurator - 单独运行")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # 初始化
        print("\n[初始化] 正在初始化存储和LLM...")
        from feishu_adapter.feishu_storage import FeishuStorage
        from core.llm.client import get_llm

        storage = FeishuStorage()
        llm = get_llm()
        print("[初始化] 成功")

        # 检查热帖库
        print("\n[检查] 正在检查热帖库...")
        from core.storage.interface import QueryFilter

        filters = [QueryFilter(field="状态", operator="eq", value="待选")]
        trends = storage.query("热帖库", filters=filters, limit=150)
        print(f"[检查] 热帖库中有 {len(trends)} 条待选热帖")

        if len(trends) == 0:
            print("\n[警告] 热帖库为空，需要先运行小哨抓取热帖!")
            print("是否先运行小哨?(y/n): ")
            # 自动运行小哨
            print("[自动] 正在运行小哨...")
            from core.agents.trend_scout import TrendScoutAgent
            agent = TrendScoutAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001"})
            print(f"[小哨] 完成: 抓取 {result.get('count', 0)} 条热帖")

            # 重新查询
            trends = storage.query("热帖库", filters=filters, limit=150)
            print(f"[检查] 热帖库现在有 {len(trends)} 条待选热帖")

        # 运行小编
        print("\n" + "=" * 70)
        print("[运行] 小编开始选题...")
        print("=" * 70)

        def run_topic_curator():
            from core.agents.topic_curator import TopicCuratorAgent
            agent = TopicCuratorAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001"})
            return result

        result = retry_operation(run_topic_curator, max_retries=5, delay=3)

        if result:
            print(f"\n✅ 小编完成: 生成 {result.get('count', 0)} 条选题")

            # 检查生成的选题
            filters = [QueryFilter(field="状态", operator="eq", value="已选")]
            topics = storage.query("选题库", filters=filters, limit=10)
            print(f"\n[结果] 选题库现在有 {len(topics)} 条已选选题:")

            for i, topic in enumerate(topics, 1):
                data = topic.data
                print(f"\n  [{i}] {data.get('选题标题', '无标题')}")
                print(f"      ID: {data.get('id', 'N/A')}")
                print(f"      角度: {data.get('选题角度', 'N/A')[:50]}...")
                print(f"      爆点: {data.get('预估爆点', 'N/A')[:50]}...")
                print(f"      优先级: {data.get('推荐优先级', 'N/A')}")
                print(f"      创建时间: {datetime.fromtimestamp(data.get('创建时间', 0)/1000).strftime('%Y-%m-%d %H:%M') if data.get('创建时间') else 'N/A'}")
        else:
            print("\n❌ 小编运行失败")

        print("\n" + "=" * 70)
        print("[完成]")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
