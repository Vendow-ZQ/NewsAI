#!/usr/bin/env python3
"""
完整流程测试 + 验证
跑一遍小哨→小编→生产组→小审→小发→mock数据→小数
然后读取飞书Base验证数据完整性
"""

import sys
import os
import asyncio

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter


async def run_pipeline():
    storage = FeishuStorage()
    llm = get_llm()

    print("=" * 70)
    print("STEP 0: Clean up - 重置热帖库状态")
    print("=" * 70)
    try:
        all_trends = storage.query("热帖库", limit=500)
        for t in all_trends:
            tid = t.data.get("id", "")
            if tid:
                storage.update("热帖库", tid, {"状态": "待选"})
        print(f"  重置了 {len(all_trends)} 条热帖为'待选'")
    except Exception as e:
        print(f"  警告: {e}")

    print("\n" + "=" * 70)
    print("STEP 1: 小哨 TrendScout - 抓取热帖")
    print("=" * 70)
    from core.agents.trend_scout import TrendScoutAgent
    scout = TrendScoutAgent(storage, llm)
    scout_result = scout.execute({})
    print(f"  抓取热帖: {scout_result.get('count', 0)} 条")

    print("\n" + "=" * 70)
    print("STEP 2: 小编 TopicCurator - 选择选题")
    print("=" * 70)
    from core.agents.topic_curator import TopicCuratorAgent
    curator = TopicCuratorAgent(storage, llm)
    topic_result = curator.execute({"koc_id": "KOC-001"})
    print(f"  生成选题: {topic_result.get('count', 0)} 条")

    # 获取刚创建的选题
    topics = storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="已选")], limit=5)
    if not topics:
        print("ERROR: 小编没有创建选题")
        return
    topic = topics[0].data
    topic_id = topic.get("id", "")
    topic_title = topic.get("选题标题", "")
    print(f"  选题ID: {topic_id}")
    print(f"  选题标题: {topic_title}")

    print("\n" + "=" * 70)
    print("STEP 3: 生产组并行 - 小文/小图/小播")
    print("=" * 70)

    from core.agents.content_writer import ContentWriterAgent
    from core.agents.visual_designer import VisualDesignerAgent
    from core.agents.script_writer import ScriptWriterAgent

    async def run_writer():
        agent = ContentWriterAgent(storage, llm)
        return agent.execute({"topic_id": topic_id, "koc_id": "KOC-001"})

    async def run_visual():
        agent = VisualDesignerAgent(storage, llm)
        return agent.execute({"topic_id": topic_id, "koc_id": "KOC-001"})

    async def run_script():
        agent = ScriptWriterAgent(storage, llm)
        return agent.execute({"topic_id": topic_id, "koc_id": "KOC-001"})

    writer_r, visual_r, script_r = await asyncio.gather(
        run_writer(), run_visual(), run_script(),
        return_exceptions=True
    )

    print(f"  小文: {'OK' if not isinstance(writer_r, Exception) else f'FAIL: {writer_r}'}")
    print(f"  小图: {'OK' if not isinstance(visual_r, Exception) else f'FAIL: {visual_r}'}")
    print(f"  小播: {'OK' if not isinstance(script_r, Exception) else f'FAIL: {script_r}'}")

    print("\n" + "=" * 70)
    print("STEP 4: 小审 Reviewer - 审查内容")
    print("=" * 70)
    from core.agents.reviewer import ReviewerAgent
    reviewer = ReviewerAgent(storage, llm)
    review_result = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    verdict = review_result.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
    print(f"  审查结论: {verdict}")

    # 如果需要修改，跑小改
    if verdict == "需修改":
        print("\n" + "=" * 70)
        print("STEP 4b: 小改 Editor - 修改内容")
        print("=" * 70)
        from core.agents.editor import EditorAgent
        editor = EditorAgent(storage, llm)
        edit_result = editor.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        print(f"  修改完成: {edit_result.get('count', 0)} 条")

        # 再审一次
        print("\n  小审再审...")
        review_result2 = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        verdict2 = review_result2.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
        print(f"  再审结论: {verdict2}")

    print("\n" + "=" * 70)
    print("STEP 5: 小发 Distributor - 分发计划")
    print("=" * 70)
    from core.agents.distributor import DistributorAgent
    distributor = DistributorAgent(storage, llm)
    dist_result = distributor.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    print(f"  分发完成: {dist_result.get('count', 0)} 条")

    print("\n" + "=" * 70)
    print("STEP 6: Mock数据 - 生成平台数据")
    print("=" * 70)
    import subprocess
    r = subprocess.run([sys.executable, "scripts/mock_analytics_data.py"], capture_output=True, text=True)
    print(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)
    if r.stderr:
        print(f"  stderr: {r.stderr[:300]}")

    print("\n" + "=" * 70)
    print("STEP 7: 小数 Analyst - 数据分析")
    print("=" * 70)
    from core.agents.analyst import AnalystAgent
    analyst = AnalystAgent(storage, llm)
    # 强制测试模式，不检查24小时
    analyst_result = analyst.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    print(f"  分析完成: {analyst_result.get('count', 0)} 条")

    return topic_id


def verify_tables(storage, topic_id):
    """验证各表数据完整性"""
    print("\n" + "=" * 70)
    print("VERIFICATION: 数据完整性检查")
    print("=" * 70)

    issues = []

    # 1. 检查热帖库
    print("\n[1] 热帖库检查")
    trends = storage.query("热帖库", limit=20)
    print(f"  记录数: {len(trends)}")
    for t in trends[:3]:
        d = t.data
        missing = [f for f in ["标题", "原文摘要", "原文语言", "主题标签", "阅览量", "互动量", "发布时间", "抓取时间", "热度评分", "内容质量", "状态"] if not d.get(f)]
        if missing:
            issues.append(f"热帖 {d.get('id', '')[:20]} 缺少字段: {missing}")
    if not issues:
        print("  前3条热帖字段完整")
    else:
        for i in issues[:5]:
            print(f"  ISSUE: {i}")

    # 2. 检查选题库
    print("\n[2] 选题库检查")
    topics = storage.query("选题库", limit=10)
    print(f"  记录数: {len(topics)}")
    for t in topics[:3]:
        d = t.data
        print(f"  选题: {d.get('选题标题', 'N/A')[:40]}...")
        print(f"    状态: {d.get('状态', 'N/A')}")
        print(f"    创建者Agent: {d.get('创建者Agent', 'N/A')}")
        print(f"    帖子文档链接: {'有' if d.get('帖子文档链接') else '无'}")
        print(f"    配图方案文档链接: {'有' if d.get('配图方案文档链接') else '无'}")
        print(f"    视频脚本文档链接: {'有' if d.get('视频脚本文档链接') else '无'}")
        print(f"    审改文档链接: {'有' if d.get('审改文档链接') else '无'}")
        print(f"    数据回流ID: {d.get('数据回流ID', '无')}")

    # 3. 检查数据库
    print("\n[3] 数据库检查")
    data_records = storage.query("数据库", limit=10)
    print(f"  记录数: {len(data_records)}")
    for r in data_records[:3]:
        d = r.data
        print(f"  选题: {d.get('选题标题', 'N/A')[:40]}...")
        print(f"    综合评分: {d.get('综合评分', 'N/A')}")
        print(f"    爆点验证: {d.get('爆点验证', 'N/A')}")
        print(f"    公众号阅读量: {d.get('公众号_阅读量', 'N/A')}")
        print(f"    抖音播放量: {d.get('抖音_播放量', 'N/A')}")

    # 4. 检查Agent协作日志
    print("\n[4] Agent协作日志检查")
    logs = storage.query("Agent协作日志", limit=20)
    print(f"  记录数: {len(logs)}")
    for log in logs[:5]:
        d = log.data
        print(f"  {d.get('Agent花名', 'N/A')} | {d.get('任务类型', 'N/A')} | {d.get('执行状态', 'N/A')} | {d.get('输出摘要', 'N/A')[:50]}")

    return issues


def verify_docs(storage, topic_id):
    """验证文档内容"""
    print("\n" + "=" * 70)
    print("VERIFICATION: 文档内容检查")
    print("=" * 70)

    from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
    doc_storage = FeishuDocStorage()

    topic = storage.get_by_id("选题库", topic_id)
    if not topic:
        print("  选题不存在")
        return

    d = topic.data

    # 1. 帖子文档
    print("\n[1] 帖子文档")
    post_url = d.get("帖子文档链接", "")
    if post_url:
        try:
            url_str = post_url.get('link', '') if isinstance(post_url, dict) else post_url
            doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
            content = doc_storage.read_doc_content(doc_id)
            print(f"  文档长度: {len(content)} 字符")
            print(f"  包含公众号: {'公众号' in content}")
            print(f"  包含小红书: {'小红书' in content}")
            print(f"  包含抖音: {'抖音' in content}")
            print(f"  包含B站: {'B站' in content}")
            print(f"  前200字符:\n  {content[:200]}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print("  无帖子文档链接")

    # 2. 配图方案文档
    print("\n[2] 配图方案文档")
    visual_url = d.get("配图方案文档链接", "")
    if visual_url:
        try:
            url_str = visual_url.get('link', '') if isinstance(visual_url, dict) else visual_url
            doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
            content = doc_storage.read_doc_content(doc_id)
            print(f"  文档长度: {len(content)} 字符")
            print(f"  前200字符:\n  {content[:200]}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print("  无配图方案文档链接")

    # 3. 视频脚本文档
    print("\n[3] 视频脚本文档")
    script_url = d.get("视频脚本文档链接", "")
    if script_url:
        try:
            url_str = script_url.get('link', '') if isinstance(script_url, dict) else script_url
            doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
            content = doc_storage.read_doc_content(doc_id)
            print(f"  文档长度: {len(content)} 字符")
            print(f"  前200字符:\n  {content[:200]}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print("  无视频脚本文档链接")

    # 4. 审改文档
    print("\n[4] 审改文档")
    audit_url = d.get("审改文档链接", "")
    if audit_url:
        try:
            url_str = audit_url.get('link', '') if isinstance(audit_url, dict) else audit_url
            doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
            content = doc_storage.read_doc_content(doc_id)
            print(f"  文档长度: {len(content)} 字符")
            print(f"  前200字符:\n  {content[:200]}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print("  无审改文档链接")


async def main():
    print("=" * 70)
    print("NewsAI 完整流程测试 + 验证")
    print("=" * 70)

    storage = FeishuStorage()

    # Run pipeline
    topic_id = await run_pipeline()

    # Verify
    verify_tables(storage, topic_id)
    verify_docs(storage, topic_id)

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
