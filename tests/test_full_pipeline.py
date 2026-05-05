#!/usr/bin/env python3
"""快速验证完整流程 - 跳过爬虫，直接用种子热帖数据"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter


async def run_full_pipeline():
    """运行完整流程：小编 -> 小文/小图/小播 -> 小审 -> 小发"""

    storage = FeishuStorage()
    llm = get_llm()

    # 1. 检查热帖库（种子数据）
    print("=" * 60)
    print("[1/6] 检查热帖库...")
    filters = [QueryFilter(field="状态", operator="eq", value="待选")]
    trends = storage.query("热帖库", filters=filters, limit=10)
    print(f"  待选热帖: {len(trends)}条")

    if not trends:
        print("❌ 没有待选热帖，流程无法继续")
        return

    for t in trends[:3]:
        print(f"    - {t.data.get('标题', 'N/A')[:50]}...")

    # 2. 运行小编Agent
    print("\n" + "=" * 60)
    print("[2/6] 运行小编Agent...")
    from core.agents.topic_curator import TopicCuratorAgent

    topic_agent = TopicCuratorAgent(storage, llm)
    topic_result = topic_agent.execute({"koc_id": "KOC-001"})
    print(f"  ✅ 小编生成选题: {topic_result.get('count', 0)}条")

    # 检查生成的选题
    topics = storage.query("选题库", filters=[], limit=10)
    if not topics:
        print("❌ 小编未创建选题")
        return

    topic_id = topics[0].data.get("业务ID")
    topic_title = topics[0].data.get("选题标题")
    print(f"  使用选题: {topic_id} - {topic_title[:40]}...")

    # 3. 并发运行生产组：小文、小图、小播
    print("\n" + "=" * 60)
    print("[3/6] 并发运行生产组 (小文/小图/小播)...")

    from core.agents.content_writer import ContentWriterAgent
    from core.agents.visual_designer import VisualDesignerAgent
    from core.agents.script_writer import ScriptWriterAgent

    async def run_writer():
        agent = ContentWriterAgent(storage, llm)
        return agent.execute({"topic_id": topic_id})

    async def run_visual():
        agent = VisualDesignerAgent(storage, llm)
        return agent.execute({"topic_id": topic_id})

    async def run_script():
        agent = ScriptWriterAgent(storage, llm)
        return agent.execute({"topic_id": topic_id})

    # 并发执行
    writer_result, visual_result, script_result = await asyncio.gather(
        run_writer(), run_visual(), run_script(),
        return_exceptions=True
    )

    print(f"  小文: {'✅ 完成' if not isinstance(writer_result, Exception) else '❌ 失败'}")
    print(f"  小图: {'✅ 完成' if not isinstance(visual_result, Exception) else '❌ 失败'}")
    print(f"  小播: {'✅ 完成' if not isinstance(script_result, Exception) else '❌ 失败'}")

    # 4. 运行小审
    print("\n" + "=" * 60)
    print("[4/6] 运行小审Agent...")
    from core.agents.reviewer import ReviewerAgent

    review_agent = ReviewerAgent(storage, llm)
    review_result = review_agent.execute({"topic_id": topic_id})
    verdict = review_result.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
    print(f"  ✅ 小审查审查结论: {verdict}")

    # 5. 运行小发
    print("\n" + "=" * 60)
    print("[5/6] 运行小发Agent...")
    from core.agents.distributor import DistributorAgent

    dist_agent = DistributorAgent(storage, llm)
    dist_result = dist_agent.execute({"topic_id": topic_id})
    print(f"  ✅ 小发生成分发计划")

    # 6. 检查结果
    print("\n" + "=" * 60)
    print("[6/6] 检查结果...")

    # 重新查询选题
    topics = storage.query("选题库", filters=[QueryFilter(field="业务ID", operator="eq", value=topic_id)], limit=1)
    if topics:
        fields = topics[0].data
        print(f"  选题标题: {fields.get('选题标题', 'N/A')}")
        print(f"  状态: {fields.get('状态', 'N/A')}")
        print(f"  帖子内容: {'✅ 有' if fields.get('帖子内容') else '❌ 无'}")
        print(f"  视频脚本: {'✅ 有' if fields.get('视频脚本内容') else '❌ 无'}")
        print(f"  审改记录: {'✅ 有' if fields.get('审改记录') else '❌ 无'}")
        print(f"  分发计划: {'✅ 有' if fields.get('分发计划') else '❌ 无'}")

    print("\n" + "=" * 60)
    print("🎉 完整流程验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
