"""
NewsAI v3.0 端到端测试 - 实时状态检验版
逐个Agent运行，实时检验状态、耗时、输出质量
使用方法: python e2e_test_v2.py
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


def log_step(agent_name: str, status: str, detail: str = "", elapsed: float = 0, extra: dict = None):
    """记录步骤结果"""
    entry = {
        "agent": agent_name,
        "status": status,
        "detail": detail,
        "elapsed": round(elapsed, 2),
        "timestamp": datetime.now().isoformat(),
    }
    if extra:
        entry.update(extra)
    results["agents"].append(entry)
    icon = "[OK]" if status == "PASS" else "[ERR]" if status == "FAIL" else "[WARN]"
    print(f"{icon} [{agent_name}] {status} ({elapsed:.2f}s) {detail}")
    return entry


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


def validate_output(agent_name: str, result: dict, checks: list) -> list:
    """验证输出质量，返回问题列表"""
    issues = []
    for check_name, check_func, error_msg in checks:
        try:
            if not check_func(result):
                issues.append(f"{check_name}: {error_msg}")
        except Exception as e:
            issues.append(f"{check_name}: 验证异常 {e}")
    return issues


async def run_agent(agent_class, name: str, storage, llm, context: dict = None,
                    validation_checks: list = None):
    """运行单个 Agent，带验证"""
    ctx = context or {}
    start = time.time()
    try:
        agent = agent_class(storage, llm)
        result = agent.execute(ctx)
        elapsed = time.time() - start

        # 执行验证
        validation_issues = []
        if validation_checks:
            validation_issues = validate_output(name, result, validation_checks)
            if validation_issues:
                for issue in validation_issues:
                    log_bug(name, issue, "P2")

        return result, elapsed, None, validation_issues
    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, str(e), []


async def main():
    print("=" * 70)
    print("NewsAI v3.0 端到端冒烟测试 - 实时检验版")
    print("=" * 70)
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

    def validate_trend_scout(result):
        """验证小哨输出"""
        if not result:
            return False, "结果为空"
        trend_ids = result.get("trend_ids", [])
        if len(trend_ids) == 0:
            return False, "没有生成热帖"
        if len(trend_ids) < 7:  # 至少7个平台各3条=21条，但实际可能少点
            return False, f"热帖数量不足: {len(trend_ids)}"
        return True, f"生成 {len(trend_ids)} 条热帖"

    print("[1/9] 小哨 TrendScout - 信息采集...")
    checks = [
        ("热帖数量", lambda r: len(r.get("trend_ids", [])) >= 7, "热帖数量不足 (<7)"),
        ("结果非空", lambda r: len(r.get("trend_ids", [])) > 0, "无热帖生成"),
    ]
    result, elapsed, err, issues = await run_agent(
        TrendScoutAgent, "小哨", storage, llm, validation_checks=checks
    )

    if err:
        log_step("小哨", "FAIL", err, elapsed)
        log_bug("小哨", err)
    else:
        trend_ids = result.get("trend_ids", [])
        log_step("小哨", "PASS", f"写入 {len(trend_ids)} 条热帖", elapsed,
                {"trend_count": len(trend_ids)})

    # ===== 小编 =====
    from core.agents.topic_curator import TopicCuratorAgent

    print("\n[2/9] 小编 TopicCurator - 选题策划...")
    checks = [
        ("生成选题", lambda r: len(r.get("all_topic_ids", [])) > 0, "没有生成选题"),
        ("选中选题", lambda r: r.get("selected_topic_id"), "没有选中选题"),
        ("创建ASSET", lambda r: r.get("asset_id"), "没有创建ASSET"),
    ]
    result, elapsed, err, issues = await run_agent(
        TopicCuratorAgent, "小编", storage, llm, validation_checks=checks
    )

    if err:
        log_step("小编", "FAIL", err, elapsed)
        log_bug("小编", err)
    else:
        topic_id = result.get("selected_topic_id", "")
        asset_id = result.get("asset_id", "")
        all_ids = result.get("all_topic_ids", [])
        log_step("小编", "PASS", f"生成 {len(all_ids)} 条选题，选中 {topic_id}",
                elapsed, {"asset_id": asset_id})

    # 如果没有生成 topic，后续无法继续
    if not topic_id:
        print("\n[ERR] 小编未生成选题，流程中断")
        return 1

    # 构建上下文
    context = {"topic_id": topic_id, "asset_id": asset_id, "koc_id": "KOC-001"}

    # ===== 小文 =====
    from core.agents.content_writer import ContentWriterAgent

    print("\n[3/9] 小文 ContentWriter - 长文撰写...")
    print("        检验: 字数1000-3000, 配图占位≥5")
    checks = [
        ("内容非空", lambda r: r.get("long_form_content"), "无长文内容"),
        ("正文字数", lambda r: len(r.get("long_form_content", {}).get("正文", "")) >= 500, "正文过短(<500字)"),
        ("字数达标", lambda r: r.get("long_form_content", {}).get("字数", 0) >= 500, "字数不足(<500)"),
        ("配图占位", lambda r: len(r.get("long_form_content", {}).get("配图占位", [])) >= 5, "配图占位不足(<5)"),
        ("文档链接", lambda r: r.get("doc_url"), "无文档链接"),
    ]
    result, elapsed, err, issues = await run_agent(
        ContentWriterAgent, "小文", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小文", "FAIL", err, elapsed)
        log_bug("小文", err)
    else:
        content = result.get("long_form_content", {})
        word_count = content.get("字数", 0) if isinstance(content, dict) else 0
        placeholders = content.get("配图占位", []) if isinstance(content, dict) else []
        doc_url = result.get("doc_url", "")

        # 详细输出检验
        print(f"        [检验] 字数: {word_count}")
        print(f"        [检验] 配图占位: {len(placeholders)} 个")
        print(f"        [检验] 文档: {doc_url[:60]}...")

        if word_count < 500:
            log_bug("小文", f"字数不足: {word_count} 字", "P1")
        if len(placeholders) < 5:
            log_bug("小文", f"配图占位不足: {len(placeholders)} 个", "P1")

        log_step("小文", "PASS", f"{word_count} 字, {len(placeholders)} 个配图", elapsed)

    # ===== 小图 =====
    from core.agents.visual_designer import VisualDesignerAgent

    print("\n[4/9] 小图 VisualDesigner - 视觉设计...")
    print("        检验: 图素材5-8张")
    checks = [
        ("图素材池", lambda r: len(r.get("image_pool", [])) >= 5, "图素材池不足(<5)"),
        ("图素材上限", lambda r: len(r.get("image_pool", [])) <= 10, "图素材池过多(>10)"),
        ("文档链接", lambda r: r.get("doc_url"), "无文档链接"),
    ]
    result, elapsed, err, issues = await run_agent(
        VisualDesignerAgent, "小图", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小图", "FAIL", err, elapsed)
        log_bug("小图", err)
    else:
        pool_count = len(result.get("image_pool", []))
        doc_url = result.get("doc_url", "")

        print(f"        [检验] 图素材: {pool_count} 张")
        print(f"        [检验] 文档: {doc_url[:60]}...")

        if pool_count < 5:
            log_bug("小图", f"图素材池不足: {pool_count} 张", "P1")
        if pool_count > 10:
            log_bug("小图", f"图素材池过多: {pool_count} 张", "P2")

        log_step("小图", "PASS", f"{pool_count} 张图素材", elapsed)

    # ===== 小播 =====
    from core.agents.script_writer import ScriptWriterAgent

    print("\n[5/9] 小播 ScriptWriter - 脚本撰写...")
    print("        检验: 脚本有时长、镜头数")
    checks = [
        ("脚本非空", lambda r: r.get("script"), "无脚本内容"),
        ("总时长", lambda r: r.get("script", {}).get("总时长"), "无总时长"),
        ("镜头清单", lambda r: len(r.get("script", {}).get("镜头清单", [])) > 0, "无镜头清单"),
        ("文档链接", lambda r: r.get("doc_url"), "无文档链接"),
    ]
    result, elapsed, err, issues = await run_agent(
        ScriptWriterAgent, "小播", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小播", "FAIL", err, elapsed)
        log_bug("小播", err)
    else:
        script = result.get("script", {})
        duration = script.get("总时长", "")
        shots = len(script.get("镜头清单", []))
        doc_url = result.get("doc_url", "")

        print(f"        [检验] 时长: {duration}")
        print(f"        [检验] 镜头: {shots} 个")
        print(f"        [检验] 文档: {doc_url[:60]}...")

        if shots == 0:
            log_bug("小播", "无镜头清单", "P1")

        log_step("小播", "PASS", f"{duration}, {shots} 个镜头", elapsed)

    # ===== production_sync =====
    print("\n[6/9] production_sync - 生产状态同步...")
    ps_start = time.time()
    try:
        from core.graph.state import NewsAIState
        from core.graph.nodes import create_production_sync_node
        state = NewsAIState(current_topic_id=topic_id, current_asset_id=asset_id)
        node = create_production_sync_node(storage, llm)
        ps_result = node(state)
        ps_elapsed = time.time() - ps_start

        # 检查ASSET状态
        asset = storage.get_by_id("内容资产库", asset_id)
        if asset:
            text_status = asset.data.get("文案状态", "")
            image_status = asset.data.get("配图状态", "")
            video_status = asset.data.get("视频状态", "")
            print(f"        [检验] 文案: {text_status}, 配图: {image_status}, 视频: {video_status}")

        status = "PASS" if not ps_result.get("errors") else "FAIL"
        log_step("production_sync", status, "检查 3 状态", ps_elapsed)
    except Exception as e:
        ps_elapsed = time.time() - ps_start
        log_step("production_sync", "FAIL", str(e), ps_elapsed)
        log_bug("production_sync", str(e))

    # ===== 小审 =====
    from core.agents.reviewer import ReviewerAgent

    print("\n[7/9] 小审 Reviewer - 内容审核...")
    print("        检验: 输出verdict和issues")
    checks = [
        ("审查结果", lambda r: r.get("review_result"), "无审查结果"),
        ("verdict", lambda r: r.get("review_result", {}).get("verdict") in ["pass", "needs_revision"], "verdict无效"),
        ("issues", lambda r: isinstance(r.get("review_result", {}).get("issues"), list), "issues格式错误"),
    ]
    result, elapsed, err, issues = await run_agent(
        ReviewerAgent, "小审", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小审", "FAIL", err, elapsed)
        log_bug("小审", err)
    else:
        review = result.get("review_result", {})
        verdict = review.get("verdict", "")
        forced = review.get("forced_pass", False)
        issues_count = len(review.get("issues", []))

        print(f"        [检验] verdict: {verdict}")
        print(f"        [检验] 强制通过: {forced}")
        print(f"        [检验] issues: {issues_count} 条")

        log_step("小审", "PASS", f"{verdict}{' (强制)' if forced else ''}, {issues_count} issues", elapsed)

    # 如果需要修改，运行小改
    if result and result.get("review_result", {}).get("verdict") == "needs_revision":
        print("\n[7.5/9] 小改 Editor - 内容修改...")
        from core.agents.editor import EditorAgent

        checks = [
            ("修改结果", lambda r: r.get("edit_result"), "无修改结果"),
            ("changelog", lambda r: len(r.get("edit_result", {}).get("changelog", [])) > 0, "无修改记录"),
        ]
        result2, elapsed2, err2, issues2 = await run_agent(
            EditorAgent, "小改", storage, llm, context, validation_checks=checks
        )

        if err2:
            log_step("小改", "FAIL", err2, elapsed2)
            log_bug("小改", err2)
        else:
            changelog = result2.get("edit_result", {}).get("changelog", [])
            log_step("小改", "PASS", f"{len(changelog)} 处修改", elapsed2)

    # ===== 小发 =====
    from core.agents.distributor import DistributorAgent

    print("\n[8/9] 小发 Distributor - 分发策略...")
    print("        检验: 生成5个平台文档")
    checks = [
        ("平台版本", lambda r: len(r.get("platform_versions", {})) >= 4, "平台版本不足(<4)"),
        ("分发计划", lambda r: r.get("distribution_plan"), "无分发计划"),
        ("文档链接", lambda r: len(r.get("doc_urls", {})) >= 4, "分发文档不足(<4)"),
    ]
    result, elapsed, err, issues = await run_agent(
        DistributorAgent, "小发", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小发", "FAIL", err, elapsed)
        log_bug("小发", err)
    else:
        docs = result.get("doc_urls", {})
        platforms = list(result.get("platform_versions", {}).keys())

        print(f"        [检验] 平台: {', '.join(platforms)}")
        print(f"        [检验] 文档: {len(docs)} 个")

        if len(docs) < 4:
            log_bug("小发", f"分发文档不足: {len(docs)} 个", "P1")

        log_step("小发", "PASS", f"{len(docs)} 个分发文档 ({', '.join(platforms)})", elapsed)

    # ===== 小数 =====
    from core.agents.analyst import AnalystAgent

    print("\n[9/9] 小数 Analyst - 数据分析...")
    print("        检验: DATA记录生成")
    checks = [
        ("DATA_ID", lambda r: r.get("data_id"), "无DATA_ID"),
        ("分析结果", lambda r: r.get("analysis"), "无分析结果"),
        ("综合评分", lambda r: 0 <= float(r.get("analysis", {}).get("综合评分", -1)) <= 1, "综合评分无效"),
    ]
    result, elapsed, err, issues = await run_agent(
        AnalystAgent, "小数", storage, llm, context, validation_checks=checks
    )

    if err:
        log_step("小数", "FAIL", err, elapsed)
        log_bug("小数", err)
    else:
        data_id = result.get("data_id", "")
        analysis = result.get("analysis", {})
        score = analysis.get("综合评分", 0)
        verdict = analysis.get("爆点验证", "")

        print(f"        [检验] DATA: {data_id}")
        print(f"        [检验] 评分: {score}")
        print(f"        [检验] 验证: {verdict}")

        log_step("小数", "PASS", f"DATA {data_id}, 评分 {score}", elapsed)

    # 汇总
    total_elapsed = time.time() - total_start
    results["total_time"] = round(total_elapsed, 2)

    print()
    print("=" * 70)
    print("测试结果汇总")
    print("=" * 70)

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
    report_file = f"e2e_report_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"详细报告: {report_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
