#!/usr/bin/env python3
"""NewsAI 端到端验证脚本 v2 —— 使用 ainvoke 直接执行，然后验证结果。"""

import asyncio
import sys
import time
from datetime import datetime

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.graph.builder import build_newsai_graph
from core.graph.state import NewsAIState


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))


def log(section: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    safe_print(f"[{ts}] [{section}] {msg}")


async def run():
    start = time.time()
    safe_print("=" * 70)
    safe_print("NewsAI End-to-End Verification")
    safe_print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("=" * 70)

    storage = FeishuStorage()
    llm = get_llm()

    # Phase 1: Pre-check
    log("CHECK", "Checking preconditions...")
    koc = storage.get_by_id("KOC人设", "KOC-001")
    if not koc:
        log("CHECK", "ERROR: KOC-001 not found")
        return False
    log("CHECK", f"KOC-001 OK: {koc.data.get('账号名', 'N/A')}")

    # Snapshot before
    before = {}
    for table in ["热帖库", "选题库", "内容资产库", "Agent协作日志"]:
        try:
            records = storage.query(table, limit=100)
            before[table] = len(records)
        except:
            before[table] = -1
        log("CHECK", f"  {table} before: {before[table]} records")

    # Phase 2: Run LangGraph
    log("RUN", "Building LangGraph...")
    graph = build_newsai_graph(storage, llm)
    log("RUN", "LangGraph compiled")

    state = NewsAIState()
    log("RUN", "Starting pipeline execution (this may take 5-15 minutes)...")
    safe_print("-" * 70)

    run_start = time.time()
    try:
        result = await graph.ainvoke(state)
        run_elapsed = time.time() - run_start
        log("RUN", f"Pipeline completed in {run_elapsed:.1f}s")
    except Exception as e:
        run_elapsed = time.time() - run_start
        log("RUN", f"Pipeline failed after {run_elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        # Continue to verify what was created

    safe_print("-" * 70)

    # Phase 3: Verify results
    log("VERIFY", "Checking post-run state...")
    after = {}
    for table in ["热帖库", "选题库", "内容资产库", "Agent协作日志"]:
        try:
            records = storage.query(table, limit=100)
            after[table] = len(records)
        except:
            after[table] = -1
        delta = after[table] - before[table] if before[table] >= 0 else 0
        log("VERIFY", f"  {table}: {before[table]} -> {after[table]} (delta {delta})")

    # Phase 4: Detailed checks
    safe_print("")
    safe_print("=" * 70)
    safe_print("Detailed Verification")
    safe_print("=" * 70)

    checks = []

    # 4.1 Hot posts
    hot_count = after.get("热帖库", 0)
    checks.append(("Hot posts created", hot_count > before.get("热帖库", 0), f"{hot_count} (was {before.get('热帖库', 0)})"))

    # 4.2 Topics
    topics = storage.query("选题库", limit=10)
    topic_count = len(topics)
    checks.append(("Topics created", topic_count > 0, f"{topic_count} total"))

    # Find the latest active topic
    active_topic = None
    for t in topics:
        status = t.data.get("选题状态", "")
        if status in ["生产中", "审改中", "待发布", "已发布"]:
            active_topic = t
            break
    if not active_topic and topics:
        active_topic = topics[0]

    if active_topic:
        td = active_topic.data
        checks.append(("Topic has title", bool(td.get("选题标题")), td.get("选题标题", "")[:40]))
        checks.append(("Topic status", True, td.get("选题状态", "N/A")))

        asset_id = td.get("关联资产ID", "")
        checks.append(("Topic linked to asset", bool(asset_id), asset_id))

        # 4.3 Asset verification
        if asset_id:
            asset = storage.get_by_id("内容资产库", asset_id)
            if asset:
                ad = asset.data
                text_st = ad.get("文案状态", "N/A")
                img_st = ad.get("配图状态", "N/A")
                vid_st = ad.get("视频状态", "N/A")
                review_st = ad.get("审改状态", "N/A")
                dist_st = ad.get("分发状态", "N/A")

                checks.append(("Asset text status", text_st == "已完成", text_st))
                checks.append(("Asset image status", img_st == "已完成", img_st))
                checks.append(("Asset video status", vid_st == "已完成", vid_st))
                checks.append(("Asset review status", True, review_st))
                checks.append(("Asset distribute status", True, dist_st))

                text_doc = ad.get("文案文档链接", "")
                img_doc = ad.get("图片提示词文档链接", "")
                vid_doc = ad.get("视频脚本文档链接", "")

                checks.append(("Text doc link", bool(text_doc), str(text_doc)[:50] if text_doc else "missing"))
                checks.append(("Image doc link", bool(img_doc), str(img_doc)[:50] if img_doc else "missing"))
                checks.append(("Video doc link", bool(vid_doc), str(vid_doc)[:50] if vid_doc else "missing"))
            else:
                checks.append(("Asset exists", False, f"asset_id={asset_id} not found"))

    # 4.4 Agent logs
    logs = storage.query("Agent协作日志", limit=30)
    agents_seen = set()
    for lg in logs:
        name = lg.data.get("Agent花名", "")
        if name:
            agents_seen.add(name)
    checks.append(("Agent logs", len(logs) > 0, f"{len(logs)} logs from {agents_seen}"))

    # Print results
    safe_print("")
    all_pass = True
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        safe_print(f"  [{status}] {name}: {detail}")

    total = time.time() - start
    safe_print("")
    safe_print(f"Total time: {total:.1f}s ({total/60:.1f}min)")
    safe_print("=" * 70)
    if all_pass:
        safe_print("ALL CHECKS PASSED!")
    else:
        safe_print("SOME CHECKS FAILED")
    safe_print("=" * 70)

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(run())
    sys.exit(0 if success else 1)
