"""
NewsAI v3.0 端到端冒烟测试

逐个 Agent 运行，记录每一步用时和结果。
使用方法: python e2e_test.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).parent / ".env")

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.llm.client import get_llm
from feishu_adapter.feishu_storage import FeishuStorage

# 测试结果记录
results = {
    "start_time": datetime.now().isoformat(),
    "agents": [],
    "total_time": 0,
    "bugs": [],
}


def log_step(agent_name: str, status: str, detail: str = "", elapsed: float = 0):
    """记录步骤结果"""
    entry = {
        "agent": agent_name,
        "status": status,
        "detail": detail,
        "elapsed": round(elapsed, 2),
        "timestamp": datetime.now().isoformat(),
    }
    results["agents"].append(entry)
    icon = "[OK]" if status == "PASS" else "[ERR]" if status == "FAIL" else "[...]"
    print(f"{icon} [{agent_name}] {status} ({elapsed:.2f}s) {detail}")


def log_bug(agent_name: str, description: str, severity: str = "P1"):
    """记录 bug"""
    bug = {
        "agent": agent_name,
        "severity": severity,
        "description": description,
        "timestamp": datetime.now().isoformat(),
    }
    results["bugs"].append(bug)
    print(f"  [BUG] [{severity}] {agent_name}: {description}")


async def run_agent(agent_class, name: str, storage, llm, context: dict = None):
    """运行单个 Agent，返回 (result, elapsed)"""
    ctx = context or {}
    start = time.time()
    try:
        agent = agent_class(storage, llm)
        result = agent.execute(ctx)
        elapsed = time.time() - start
        return result, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, str(e)


async def main():
    print("=" * 60)
    print("NewsAI v3.0 端到端冒烟测试")
    print("=" * 60)
    print()

    # 检查环境变量
    required_env = ["LARK_APP_ID", "LARK_APP_SECRET", "LARK_BASE_APP_TOKEN", "LLM_API_KEY"]
    missing = [k for k in required_env if not os.getenv(k)]
    if missing:
        print(f"[ERR] 缺少环境变量: {missing}")
        return 1
    print("[OK] 环境变量检查通过")
    print()

    # 初始化存储和 LLM
    print("[初始化] 连接飞书 Base + LLM...")
    storage = FeishuStorage()
    llm = get_llm()
    print("[OK] 初始化完成")
    print()

    total_start = time.time()
    topic_id = ""
    asset_id = ""

    # ===== 小哨 =====
    from core.agents.trend_scout import TrendScoutAgent
    result, elapsed, err = await run_agent(TrendScoutAgent, "小哨", storage, llm)
    if err:
        log_step("小哨", "FAIL", err, elapsed)
        log_bug("小哨", err)
    else:
        trend_ids = result.get("trend_ids", [])
        log_step("小哨", "PASS", f"写入 {len(trend_ids)} 条热帖", elapsed)

    # ===== 小编 =====
    from core.agents.topic_curator import TopicCuratorAgent
    result, elapsed, err = await run_agent(TopicCuratorAgent, "小编", storage, llm)
    if err:
        log_step("小编", "FAIL", err, elapsed)
        log_bug("小编", err)
    else:
        topic_id = result.get("selected_topic_id", "")
        asset_id = result.get("asset_id", "")
        all_ids = result.get("all_topic_ids", [])
        log_step("小编", "PASS", f"生成 {len(all_ids)} 条选题，选中 {topic_id}, ASSET {asset_id}", elapsed)

    # 如果没有生成 topic，后续无法继续
    if not topic_id:
        print("\n[ERR] 小编未生成选题，流程中断")
        return 1

    # 构建上下文（传递 topic_id 和 asset_id）
    context = {"topic_id": topic_id, "asset_id": asset_id, "koc_id": "KOC-001"}

    # ===== 小文 =====
    from core.agents.content_writer import ContentWriterAgent
    result, elapsed, err = await run_agent(ContentWriterAgent, "小文", storage, llm, context)
    if err:
        log_step("小文", "FAIL", err, elapsed)
        log_bug("小文", err)
    else:
        doc_url = result.get("doc_url", "")
        log_step("小文", "PASS", f"文案文档: {doc_url[:50]}..." if doc_url else "无文档", elapsed)

    # ===== 小图 =====
    from core.agents.visual_designer import VisualDesignerAgent
    result, elapsed, err = await run_agent(VisualDesignerAgent, "小图", storage, llm, context)
    if err:
        log_step("小图", "FAIL", err, elapsed)
        log_bug("小图", err)
    else:
        pool_count = len(result.get("image_pool", []))
        doc_url = result.get("doc_url", "")
        log_step("小图", "PASS", f"{pool_count} 张图, 文档: {doc_url[:40]}..." if doc_url else f"{pool_count} 张图", elapsed)

    # ===== 小播 =====
    from core.agents.script_writer import ScriptWriterAgent
    result, elapsed, err = await run_agent(ScriptWriterAgent, "小播", storage, llm, context)
    if err:
        log_step("小播", "FAIL", err, elapsed)
        log_bug("小播", err)
    else:
        script = result.get("script", {})
        duration = script.get("总时长", "")
        doc_url = result.get("doc_url", "")
        log_step("小播", "PASS", f"{duration}, 文档: {doc_url[:40]}..." if doc_url else duration, elapsed)

    # ===== production_sync =====
    ps_start = time.time()
    try:
        from core.graph.state import NewsAIState
        from core.graph.nodes import create_production_sync_node
        state = NewsAIState(current_topic_id=topic_id, current_asset_id=asset_id)
        node = create_production_sync_node(storage, llm)
        ps_result = node(state)
        ps_elapsed = time.time() - ps_start
        status = "PASS" if not ps_result.get("errors") else "FAIL"
        log_step("production_sync", status, "检查 3 状态", ps_elapsed)
    except Exception as e:
        ps_elapsed = time.time() - ps_start
        log_step("production_sync", "FAIL", str(e), ps_elapsed)
        log_bug("production_sync", str(e))

    # ===== 小审 =====
    from core.agents.reviewer import ReviewerAgent
    result, elapsed, err = await run_agent(ReviewerAgent, "小审", storage, llm, context)
    if err:
        log_step("小审", "FAIL", err, elapsed)
        log_bug("小审", err)
    else:
        review = result.get("review_result", {})
        verdict = review.get("verdict", "")
        forced = review.get("forced_pass", False)
        log_step("小审", "PASS", f"verdict={verdict}{' (强制)' if forced else ''}", elapsed)

    # 如果需修改，运行小改（一轮）
    if result and result.get("review_result", {}).get("verdict") == "needs_revision":
        from core.agents.editor import EditorAgent
        result2, elapsed2, err2 = await run_agent(EditorAgent, "小改", storage, llm, context)
        if err2:
            log_step("小改", "FAIL", err2, elapsed2)
            log_bug("小改", err2)
        else:
            changelog = result2.get("edit_result", {}).get("changelog", [])
            log_step("小改", "PASS", f"{len(changelog)} 处修改", elapsed2)

        # 再审一轮
        result3, elapsed3, err3 = await run_agent(ReviewerAgent, "小审(v2)", storage, llm, context)
        if err3:
            log_step("小审(v2)", "FAIL", err3, elapsed3)
        else:
            verdict = result3.get("review_result", {}).get("verdict", "")
            log_step("小审(v2)", "PASS", f"verdict={verdict}", elapsed3)

    # ===== 小发 =====
    from core.agents.distributor import DistributorAgent
    result, elapsed, err = await run_agent(DistributorAgent, "小发", storage, llm, context)
    if err:
        log_step("小发", "FAIL", err, elapsed)
        log_bug("小发", err)
    else:
        docs = result.get("doc_urls", {})
        log_step("小发", "PASS", f"{len(docs)} 个分发文档", elapsed)

    # ===== 小数 =====
    from core.agents.analyst import AnalystAgent
    result, elapsed, err = await run_agent(AnalystAgent, "小数", storage, llm, context)
    if err:
        log_step("小数", "FAIL", err, elapsed)
        log_bug("小数", err)
    else:
        data_id = result.get("data_id", "")
        log_step("小数", "PASS", f"DATA {data_id}", elapsed)

    # 汇总
    total_elapsed = time.time() - total_start
    results["total_time"] = round(total_elapsed, 2)

    print()
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for r in results["agents"] if r["status"] == "PASS")
    failed = sum(1 for r in results["agents"] if r["status"] == "FAIL")
    bugs = len(results["bugs"])

    print(f"Agent 总计: {len(results['agents'])} | 通过: {passed} | 失败: {failed}")
    print(f"Bug 总计: {bugs}")
    print(f"总耗时: {total_elapsed:.2f}s")
    print()

    if bugs > 0:
        print("Bug 清单:")
        for b in results["bugs"]:
            print(f"  [{b['severity']}] {b['agent']}: {b['description']}")
        print()

    # 写入报告
    report_file = f"e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"详细报告: {report_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
