#!/usr/bin/env python3
"""完整实战流程——诚实地记录每个步骤的时间和LLM结果"""
import sys, os, asyncio, time, json
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


def log(msg):
    """带时间戳的日志输出"""
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def run_scout(storage, llm):
    log("=" * 60)
    log("STEP 1: 小哨 TrendScout —— 抓取热帖")
    log("=" * 60)
    from core.agents.trend_scout import TrendScoutAgent
    start = time.time()
    scout = TrendScoutAgent(storage, llm)
    result = scout.execute({})
    elapsed = time.time() - start
    log(f"耗时: {elapsed:.1f}s")
    log(f"抓取热帖: {result.get('count', 0)} 条")
    # 验证
    trends = storage.query("热帖库", limit=30)
    log(f"热帖库验证: {len(trends)} 条")
    for t in trends[:3]:
        d = t.data
        log(f"  [{d.get('信源平台','?')}] {d.get('标题','')[:40]}...")
        log(f"    score={d.get('热度评分')} | quality={d.get('内容质量')} | lang={d.get('原文语言')} | tags={d.get('主题标签',[])}")
    return trends


def run_curator(storage, llm):
    log("=" * 60)
    log("STEP 2: 小编 TopicCurator —— 选择选题")
    log("=" * 60)
    from core.agents.topic_curator import TopicCuratorAgent
    start = time.time()
    curator = TopicCuratorAgent(storage, llm)
    result = curator.execute({"koc_id": "KOC-001"})
    elapsed = time.time() - start
    log(f"耗时: {elapsed:.1f}s")
    log(f"生成选题: {result.get('count', 0)} 条")
    if result.get('topics'):
        t = result['topics'][0]
        log(f"选题标题: {t.get('选题标题', 'N/A')}")
        log(f"选题角度: {t.get('选题角度', 'N/A')}")
        log(f"预估爆点: {t.get('预估爆点', 'N/A')}")
        log(f"预估受众: {t.get('预估受众', 'N/A')}")
        log(f"推荐优先级: {t.get('推荐优先级', 0)}")
    # 验证
    topics = storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="已选")], limit=5)
    if not topics:
        log("ERROR: 小编未创建选题")
        return None
    topic = topics[0].data
    log(f"选题库验证:")
    log(f"  ID: {topic.get('id')}")
    log(f"  标题: {topic.get('选题标题','')[:40]}")
    log(f"  创建者Agent: {topic.get('创建者Agent','N/A')}")
    log(f"  状态: {topic.get('状态')}")
    return topic.get("id", "")


async def run_production(storage, llm, topic_id):
    log("=" * 60)
    log("STEP 3: 生产组并行 —— 小文/小图/小播")
    log("=" * 60)
    from core.agents.content_writer import ContentWriterAgent
    from core.agents.visual_designer import VisualDesignerAgent
    from core.agents.script_writer import ScriptWriterAgent

    async def writer():
        log("  [小文] 开始撰写4平台内容...")
        a = ContentWriterAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    async def visual():
        log("  [小图] 开始生成配图方案...")
        a = VisualDesignerAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    async def script():
        log("  [小播] 开始生成视频脚本...")
        a = ScriptWriterAgent(storage, llm)
        return a.execute({"topic_id": topic_id, "koc_id": "KOC-001"})

    start = time.time()
    wr, vi, sc = await asyncio.gather(writer(), visual(), script(), return_exceptions=True)
    elapsed = time.time() - start
    log(f"生产组总耗时: {elapsed:.1f}s")
    log(f"  小文: {'OK' if not isinstance(wr,Exception) else f'FAIL: {wr}'}")
    log(f"  小图: {'OK' if not isinstance(vi,Exception) else f'FAIL: {vi}'}")
    log(f"  小播: {'OK' if not isinstance(sc,Exception) else f'FAIL: {sc}'}")

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        log(f"选题库验证:")
        log(f"  帖子文档链接: {'有' if d.get('帖子文档链接') else '无'}")
        log(f"  配图方案文档链接: {'有' if d.get('配图方案文档链接') else '无'}")
        log(f"  视频脚本文档链接: {'有' if d.get('视频脚本文档链接') else '无'}")
        log(f"  状态: {d.get('状态')}")


def run_reviewer(storage, llm, topic_id):
    log("=" * 60)
    log("STEP 4: 小审 Reviewer —— 审查内容")
    log("=" * 60)
    from core.agents.reviewer import ReviewerAgent
    start = time.time()
    reviewer = ReviewerAgent(storage, llm)
    result = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    elapsed = time.time() - start
    verdict = result.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
    severity = result.get("review_results", [{}])[0].get("review_result", {}).get("严重度", "中")
    issues = result.get("review_results", [{}])[0].get("review_result", {}).get("发现的问题", [])
    log(f"耗时: {elapsed:.1f}s")
    log(f"审查结论: {verdict}")
    log(f"严重度: {severity}")
    log(f"发现问题数: {len(issues)}")
    for issue in issues[:3]:
        log(f"  - [{issue.get('位置','?')}] {issue.get('问题','')[:50]}")

    if verdict == "需修改":
        log("=" * 60)
        log("STEP 4b: 小改 Editor —— 修改内容")
        log("=" * 60)
        from core.agents.editor import EditorAgent
        start = time.time()
        editor = EditorAgent(storage, llm)
        edit_result = editor.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        elapsed = time.time() - start
        log(f"耗时: {elapsed:.1f}s")
        log(f"修改完成: {edit_result.get('count', 0)} 条")
        if edit_result.get('edit_results'):
            er = edit_result['edit_results'][0]
            log(f"修改总结: {er.get('edit_result',{}).get('修改总结','N/A')[:80]}")

        # 再审
        log("小审再审...")
        start = time.time()
        result2 = reviewer.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
        elapsed2 = time.time() - start
        verdict2 = result2.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
        log(f"再审耗时: {elapsed2:.1f}s | 结论: {verdict2}")

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        log(f"选题库验证:")
        log(f"  审改文档链接: {'有' if d.get('审改文档链接') else '无'}")
        log(f"  审改轮次: {d.get('审改轮次', 0)}")
        log(f"  状态: {d.get('状态')}")


def run_distributor(storage, llm, topic_id):
    log("=" * 60)
    log("STEP 5: 小发 Distributor —— 分发计划")
    log("=" * 60)
    from core.agents.distributor import DistributorAgent
    start = time.time()
    dist = DistributorAgent(storage, llm)
    result = dist.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    elapsed = time.time() - start
    log(f"耗时: {elapsed:.1f}s")
    log(f"分发完成: {result.get('count', 0)} 条")
    if result.get('distribution_results'):
        dr = result['distribution_results'][0]
        plan = dr.get('distribution_plan', {})
        log(f"分发策略: {plan.get('分发策略总结','N/A')[:80]}")
        platforms = plan.get('平台分发计划', [])
        for p in platforms[:4]:
            log(f"  [{p.get('平台','?')}] {p.get('发布时间','?')} | {p.get('内容形式','?')}")

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        log(f"选题库验证:")
        log(f"  状态: {d.get('状态')}")
        log(f"  分发计划: {'有' if d.get('分发计划JSON') else '无'}")


def run_mock_analytics(storage):
    log("=" * 60)
    log("STEP 6: Mock平台数据")
    log("=" * 60)
    import subprocess
    start = time.time()
    r = subprocess.run([sys.executable, "scripts/mock_analytics_data.py"], capture_output=True, text=True)
    elapsed = time.time() - start
    log(f"耗时: {elapsed:.1f}s")
    log(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)
    if r.stderr:
        log(f"stderr: {r.stderr[:200]}")


def run_analyst(storage, llm, topic_id):
    log("=" * 60)
    log("STEP 7: 小数 Analyst —— 数据分析")
    log("=" * 60)
    from core.agents.analyst import AnalystAgent
    start = time.time()
    analyst = AnalystAgent(storage, llm)
    result = analyst.execute({"topic_id": topic_id, "koc_id": "KOC-001"})
    elapsed = time.time() - start
    log(f"耗时: {elapsed:.1f}s")
    log(f"分析完成: {result.get('count', 0)} 条")
    if result.get('analyses'):
        a = result['analyses'][0]
        analysis = a.get('analysis', {})
        log(f"综合评分: {analysis.get('综合评分', 'N/A')}")
        log(f"爆点验证: {analysis.get('爆点验证', 'N/A')}")
        log(f"最佳平台: {analysis.get('平台表现',{}).get('最佳平台','N/A')}")
        log(f"成败分析: {analysis.get('成败分析','N/A')[:100]}")
        suggestions = analysis.get('选题建议', [])
        for s in suggestions[:3]:
            log(f"  建议: {s}")


def final_verify(storage, topic_id):
    log("\n" + "=" * 60)
    log("FINAL VERIFICATION")
    log("=" * 60)

    for table in ["热帖库", "选题库", "数据库", "Agent协作日志"]:
        try:
            records = storage.query(table, limit=20)
            log(f"[{table}]: {len(records)} 条")
            if records and table == "数据库":
                d = records[0].data
                log(f"  最新: {d.get('选题标题','')[:40]}... 评分:{d.get('综合评分')}")
        except Exception as e:
            log(f"[{table}]: ERROR {e}")

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        d = topic.data
        log(f"\n[选题详情]")
        log(f"  标题: {d.get('选题标题','')}")
        log(f"  状态: {d.get('状态','')}")
        log(f"  帖子文档: {'有' if d.get('帖子文档链接') else '无'}")
        log(f"  配图文档: {'有' if d.get('配图方案文档链接') else '无'}")
        log(f"  脚本文档: {'有' if d.get('视频脚本文档链接') else '无'}")
        log(f"  审改文档: {'有' if d.get('审改文档链接') else '无'}")
        log(f"  数据回流ID: {d.get('数据回流ID','无')}")

        # Read doc samples
        doc_storage = FeishuDocStorage()
        for field, name in [("帖子文档链接", "帖子"), ("配图方案文档链接", "配图"), ("视频脚本文档链接", "脚本")]:
            url = d.get(field, "")
            if url:
                try:
                    url_str = url.get('link', '') if isinstance(url, dict) else url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                    content = doc_storage.read_doc_content(doc_id)
                    log(f"  [{name}文档] {len(content)} 字符 | 前80字: {content[:80]}")
                except Exception as e:
                    log(f"  [{name}文档] 读取失败: {e}")


async def main():
    total_start = time.time()
    storage = FeishuStorage()
    llm = get_llm()

    run_scout(storage, llm)
    topic_id = run_curator(storage, llm)
    if not topic_id:
        log("Pipeline stopped: no topic selected")
        return

    await run_production(storage, llm, topic_id)
    run_reviewer(storage, llm, topic_id)
    run_distributor(storage, llm, topic_id)
    run_mock_analytics(storage)
    run_analyst(storage, llm, topic_id)
    final_verify(storage, topic_id)

    total = time.time() - total_start
    log(f"\n{'='*60}")
    log(f"TOTAL TIME: {total:.1f}s ({total/60:.1f} minutes)")
    log(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
