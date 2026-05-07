# -*- coding: utf-8 -*-
"""
完整NewsAI流程运行脚本
按顺序执行所有Agent，真实调用LLM
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 关闭mock模式
os.environ["LLM_MOCK"] = "0"

def retry_operation(func, max_retries=3, delay=2):
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

def run_pipeline():
    """运行完整流程"""
    print("=" * 70)
    print("NewsAI 完整流程运行")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # 初始化
        print("\n[初始化] 正在初始化...")
        from feishu_adapter.feishu_storage import FeishuStorage
        from core.llm.client import get_llm

        storage = FeishuStorage()
        llm = get_llm()
        print("[初始化] 存储和LLM初始化成功")

        # ========== 步骤1: 小哨 ==========
        print("\n" + "=" * 70)
        print("[步骤1/9] 小哨 TrendScout - 抓取140条热帖")
        print("=" * 70)

        def run_trend_scout():
            from core.agents.trend_scout import TrendScoutAgent
            agent = TrendScoutAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001"})
            return result

        result = retry_operation(run_trend_scout, max_retries=3)
        if result:
            print(f"✅ 小哨完成: 抓取 {result.get('count', 0)} 条热帖")
        else:
            print("❌ 小哨失败")

        # ========== 步骤2: 小编 ==========
        print("\n" + "=" * 70)
        print("[步骤2/9] 小编 TopicCurator - 从热帖中选出1条")
        print("=" * 70)

        def run_topic_curator():
            from core.agents.topic_curator import TopicCuratorAgent
            agent = TopicCuratorAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001"})
            return result

        result = retry_operation(run_topic_curator, max_retries=3)
        topic_id = None
        if result and result.get('topics'):
            topic_id = result['topics'][0].get('热帖ID') if result['topics'] else None
            print(f"✅ 小编完成: 生成 {result.get('count', 0)} 条选题")
            if topic_id:
                print(f"  关联热帖: {topic_id}")
        else:
            print("❌ 小编失败")

        # 获取刚创建的选题ID
        from core.storage.interface import QueryFilter
        filters = [QueryFilter(field="状态", operator="eq", value="已选")]
        topics = storage.query("选题库", filters=filters, limit=5)
        if topics:
            topic_id = topics[0].data.get("id")
            print(f"  选中选题ID: {topic_id}")
        else:
            print("❌ 没有找到已选状态的选题")
            return False

        # ========== 步骤3: 小文 ==========
        print("\n" + "=" * 70)
        print("[步骤3/9] 小文 ContentWriter - 撰写4平台内容")
        print("=" * 70)

        def run_content_writer():
            from core.agents.content_writer import ContentWriterAgent
            agent = ContentWriterAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_content_writer, max_retries=3)
        if result:
            print(f"✅ 小文完成: 撰写 {result.get('count', 0)} 条选题的4平台版本")
        else:
            print("❌ 小文失败")

        # ========== 步骤4: 小图 ==========
        print("\n" + "=" * 70)
        print("[步骤4/9] 小图 VisualDesigner - 设计配图方案")
        print("=" * 70)

        def run_visual_designer():
            from core.agents.visual_designer import VisualDesignerAgent
            agent = VisualDesignerAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_visual_designer, max_retries=3)
        if result:
            print(f"✅ 小图完成: 为 {result.get('count', 0)} 个选题生成配图方案")
        else:
            print("❌ 小图失败")

        # ========== 步骤5: 小播 ==========
        print("\n" + "=" * 70)
        print("[步骤5/9] 小播 ScriptWriter - 撰写视频脚本")
        print("=" * 70)

        def run_script_writer():
            from core.agents.script_writer import ScriptWriterAgent
            agent = ScriptWriterAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_script_writer, max_retries=3)
        if result:
            print(f"✅ 小播完成: 为 {result.get('count', 0)} 个选题生成视频脚本")
        else:
            print("❌ 小播失败")

        # ========== 步骤6: 小审 ==========
        print("\n" + "=" * 70)
        print("[步骤6/9] 小审 Reviewer - 审查内容")
        print("=" * 70)

        def run_reviewer():
            from core.agents.reviewer import ReviewerAgent
            agent = ReviewerAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_reviewer, max_retries=3)
        if result:
            review_results = result.get('review_results', [])
            if review_results:
                conclusion = review_results[0].get('review_result', {}).get('审查结论', '未知')
                print(f"✅ 小审完成: 审查 {result.get('count', 0)} 条选题, 结论: {conclusion}")
            else:
                print(f"✅ 小审完成: 审查 {result.get('count', 0)} 条选题")
        else:
            print("❌ 小审失败")

        # ========== 步骤7: 小改 ==========
        print("\n" + "=" * 70)
        print("[步骤7/9] 小改 Editor - 修改内容")
        print("=" * 70)

        def run_editor():
            from core.agents.editor import EditorAgent
            agent = EditorAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_editor, max_retries=3)
        if result:
            print(f"✅ 小改完成: 修改 {result.get('count', 0)} 条选题")
        else:
            print("❌ 小改失败")

        # ========== 步骤8: 小发 ==========
        print("\n" + "=" * 70)
        print("[步骤8/9] 小发 Distributor - 制定分发计划")
        print("=" * 70)

        def run_distributor():
            from core.agents.distributor import DistributorAgent
            agent = DistributorAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_distributor, max_retries=3)
        if result:
            print(f"✅ 小发完成: 制定 {result.get('count', 0)} 条选题的分发计划")
        else:
            print("❌ 小发失败")

        # ========== 步骤9: 小数 ==========
        print("\n" + "=" * 70)
        print("[步骤9/9] 小数 Analyst - 数据分析")
        print("=" * 70)

        def run_analyst():
            from core.agents.analyst import AnalystAgent
            agent = AnalystAgent(storage, llm)
            result = agent.execute({"koc_id": "KOC-001", "topic_id": topic_id})
            return result

        result = retry_operation(run_analyst, max_retries=3)
        if result:
            analyses = result.get('analyses', [])
            if analyses:
                score = analyses[0].get('analysis', {}).get('综合评分', 0)
                validation = analyses[0].get('analysis', {}).get('爆点验证', '未知')
                print(f"✅ 小数完成: 分析 {result.get('count', 0)} 条选题数据")
                print(f"  综合评分: {score}, 爆点验证: {validation}")
            else:
                print(f"✅ 小数完成: 分析 {result.get('count', 0)} 条选题数据")
        else:
            print("❌ 小数失败")

        # 总结
        print("\n" + "=" * 70)
        print("NewsAI 完整流程完成")
        print("=" * 70)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"选题ID: {topic_id}")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 流程异常: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_pipeline()
