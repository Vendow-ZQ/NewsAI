#!/usr/bin/env python3
"""快速完整流程——批量LLM优化版"""
import sys, os, asyncio, time, json
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


def cleanup(storage):
    print("=== Cleanup ===")
    for table in ["热帖库", "选题库", "数据库", "Agent协作日志"]:
        try:
            records = storage.query(table, limit=500)
            for r in records:
                rid = r.data.get("id", "")
                if rid:
                    storage.delete(table, rid)
            print(f"  清理 {table}: {len(records)} 条")
        except Exception as e:
            print(f"  跳过 {table}: {e}")


def run_scout(storage, llm):
    print("\n=== 1. 小哨 TrendScout ===")
    from core.agents.trend_scout import TrendScoutAgent
    start = time.time()
    scout = TrendScoutAgent(storage, llm)
    result = scout.execute({})
    print(f"  时间: {time.time()-start:.1f}s | 热帖: {result.get('count', 0)} 条")

    # Verify
    trends = storage.query("热帖库", limit=30)
    print(f"  热帖库验证: {len(trends)} 条")
    for t in trends[:3]:
        d = t.data
        print(f"    [{d.get('信源平台','?')}] {d.get('标题','')[:35]}... score={d.get('热度评分')} quality={d.get('内容质量')} tags={d.get('主题标签',[])}")
    return trends


def run_curator(storage, llm):
    print("\n=== 2. 小编 TopicCurator ===")
    from core.agents.topic_curator import TopicCuratorAgent
    start = time.time()
    curator = TopicCuratorAgent(storage, llm)
    result = curator.execute({"koc_id": "KOC-001"})
    elapsed = time.time() - start
    print(f"  时间: {elapsed:.1f}s | 选题: {result.get('count', 0)} 条")

    topics = storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="已选")], limit=5)
    if not topics:
        print("  ERROR: 无选题")
        return None
    topic = topics[0].data
    print(f"  选题: {topic.get('选题标题','')[:40]}...")
    print(f"  创建者Agent: {topic.get('创建者Agent','N/A')}")
    return topic.get("id", "")


async def run_production(storage, llm, topic_id):
    print("\n=== 3. 生产组并行 ===")
    from core.agents.content_writer import ContentWriterAgent
    from core.agents.visual_designer import VisualDesignerAgent
    from core.agents.script_writer import ScriptWriterAgent

    async def writer():
        a = ContentWriterAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    async def visual():
        a = VisualDesignerAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    async def script():
        a = ScriptWriterAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})

    start = time.time()
    wr, vi, sc = await asyncio.gather(writer(), visual(), script(), return_exceptions=True)
    elapsed = time.time() - start
    print(f"  时间: {elapsed:.1f}s")
    print(f"  小文: {'OK' if not isinstance(wr,Exception) else f'FAIL:{wr}'}")
    print(f"  小图: {'OK' if not isinstance(vi,Exception) else f'FAIL:{vi}'}")
    print(f"  小播: {'OK' if not isinstance(sc,Exception) else f'FAIL:{sc}'}")

    # Verify
    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        print(f"  帖子文档链接: {'有' if d.get('帖子文档链接') else '无'}")
        print(f"  配图方案文档链接: {'有' if d.get('配图方案文档链接') else '无'}")
        print(f"  视频脚本文档链接: {'有' if d.get('视频脚本文档链接') else '无'}")


def run_reviewer(storage, llm, topic_id):
    print("\n=== 4. 小审 Reviewer ===")
    from core.agents.reviewer import ReviewerAgent
    start = time.time()
    reviewer = ReviewerAgent(storage, llm)
    result = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    verdict = result.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
    print(f"  时间: {time.time()-start:.1f}s | 结论: {verdict}")

    if verdict == "需修改":
        print("\n=== 4b. 小改 Editor ===")
        from core.agents.editor import EditorAgent
        editor = EditorAgent(storage, llm)
        edit_result = editor.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        print(f"  修改完成: {edit_result.get('count', 0)} 条")

        # 再审
        result2 = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        verdict2 = result2.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
        print(f"  再审结论: {verdict2}")

    # Verify audit doc
    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        print(f"  审改文档链接: {'有' if topic.data.get('审改文档链接') else '无'}")
        print(f"  审改轮次: {topic.data.get('审改轮次', 0)}")


def run_distributor(storage, llm, topic_id):
    print("\n=== 5. 小发 Distributor ===")
    from core.agents.distributor import DistributorAgent
    start = time.time()
    dist = DistributorAgent(storage, llm)
    result = dist.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    print(f"  时间: {time.time()-start:.1f}s | 分发: {result.get('count', 0)} 条")

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        print(f"  状态: {topic.data.get('状态')}")
        print(f"  分发计划: {'有' if topic.data.get('分发计划JSON') else '无'}")


def run_mock_analytics(storage):
    print("\n=== 6. Mock平台数据 ===")
    import subprocess
    r = subprocess.run([sys.executable, "scripts/mock_analytics_data.py"], capture_output=True, text=True)
    print(r.stdout[-400:] if len(r.stdout) > 400 else r.stdout)


def run_analyst(storage, llm, topic_id):
    print("\n=== 7. 小数 Analyst ===")
    from core.agents.analyst import AnalystAgent
    start = time.time()
    analyst = AnalystAgent(storage, llm)
    result = analyst.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    print(f"  时间: {time.time()-start:.1f}s | 分析: {result.get('count', 0)} 条")

    # Verify DATA table
    data_records = storage.query("数据库", limit=5)
    print(f"  数据库验证: {len(data_records)} 条")
    for r in data_records[:2]:
        d = r.data
        print(f"    {d.get('选题标题','')[:35]}... 评分:{d.get('综合评分')} 验证:{d.get('爆点验证')}")


def verify_all(storage, topic_id):
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION")
    print("=" * 60)

    # Tables
    for table in ["热帖库", "选题库", "数据库", "Agent协作日志"]:
        try:
            records = storage.query(table, limit=20)
            print(f"\n[{table}]: {len(records)} 条")
            if records:
                d = records[0].data
                print(f"  最新记录ID: {d.get('id','N/A')}")
        except Exception as e:
            print(f"\n[{table}]: ERROR {e}")

    # Topic details
    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        print(f"\n[选题详情]")
        print(f"  标题: {d.get('选题标题','')}")
        print(f"  状态: {d.get('状态','')}")
        print(f"  帖子文档: {'有' if d.get('帖子文档链接') else '无'}")
        print(f"  配图文档: {'有' if d.get('配图方案文档链接') else '无'}")
        print(f"  脚本文档: {'有' if d.get('视频脚本文档链接') else '无'}")
        print(f"  审改文档: {'有' if d.get('审改文档链接') else '无'}")
        print(f"  数据回流ID: {d.get('数据回流ID','无')}")

    # Read doc content sample
    print("\n[文档内容抽样]")
    doc_storage = FeishuDocStorage()
    for field, name in [("帖子文档链接", "帖子"), ("配图方案文档链接", "配图"), ("视频脚本文档链接", "脚本")]:
        url = d.get(field, "") if topic else ""
        if url:
            try:
                url_str = url.get('link', '') if isinstance(url, dict) else url
                doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                content = doc_storage.read_doc_content(doc_id)
                print(f"  {name}文档: {len(content)} 字符 | 前80字: {content[:80]}")
            except Exception as e:
                print(f"  {name}文档: 读取失败 {e}")


async def main():
    storage = FeishuStorage()
    llm = get_llm()

    total_start = time.time()
    # cleanup(storage)  # Skip cleanup for speed

    trends = run_scout(storage, llm)
    topic_id = run_curator(storage, llm)
    if not topic_id:
        print("\nPipeline stopped: no topic selected")
        return

    await run_production(storage, llm, topic_id)
    run_reviewer(storage, llm, topic_id)
    run_distributor(storage, llm, topic_id)
    run_mock_analytics(storage)
    run_analyst(storage, llm, topic_id)
    verify_all(storage, topic_id)

    print(f"\n{'='*60}")
    print(f"TOTAL TIME: {time.time()-total_start:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
