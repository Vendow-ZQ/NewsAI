#!/usr/bin/env python3
"""NewsAI 端到端验证脚本。

运行完整 LangGraph 流程，记录每个 Agent 的执行时间、操作和输出，
并验证最终数据（表记录、文档）是否正确。
"""

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


class E2EVerifier:
    def __init__(self):
        self.start_time = time.time()
        self.logs = []
        self.storage = FeishuStorage()
        self.llm = get_llm()
        self.records_before = {}
        self.records_after = {}

    def _log(self, section: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{section}] {msg}"
        self.logs.append(line)
        # Windows console may not support all Unicode; encode safely
        try:
            print(line)
        except UnicodeEncodeError:
            safe = line.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            print(safe)

    def _snapshot(self, table: str) -> dict:
        """获取表的快照（ID列表和关键字段）。"""
        try:
            records = self.storage.query(table, limit=100)
            return {
                "count": len(records),
                "ids": [r.id for r in records],
                "sample": [{
                    k: v for k, v in r.data.items()
                    if k in ["id", "选题标题", "选题状态", "文案状态", "配图状态", "视频状态", "审改状态", "分发状态", "关联资产ID", "Agent花名", "任务类型", "执行状态"]
                } for r in records[:3]]
            }
        except Exception as e:
            return {"count": 0, "error": str(e)}

    async def run(self):
        print("=" * 70)
        print("NewsAI 端到端验证")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Phase 1: 前置检查
        self._log("PHASE-1", "检查前置条件...")
        koc = self.storage.get_by_id("KOC人设", "KOC-001")
        if not koc:
            self._log("PHASE-1", "ERROR: KOC-001 不存在")
            return False
        self._log("PHASE-1", f"KOC-001 存在: {koc.data.get('账号名', 'N/A')}")

        sources = self.storage.query("信源配置", limit=20)
        enabled = [s for s in sources if s.data.get("是否启用", False)]
        self._log("PHASE-1", f"信源配置: {len(sources)} 个，已启用 {len(enabled)} 个")

        # 记录运行前的表状态
        self._log("PHASE-1", "记录运行前表状态...")
        for table in ["热帖库", "选题库", "内容资产库", "Agent协作日志"]:
            self.records_before[table] = self._snapshot(table)
            self._log("PHASE-1", f"  {table}: {self.records_before[table]['count']} 条")

        # Phase 2: 构建并运行 LangGraph
        self._log("PHASE-2", "构建 LangGraph...")
        graph = build_newsai_graph(self.storage, self.llm)
        self._log("PHASE-2", "LangGraph 编译完成")

        state = NewsAIState()

        self._log("PHASE-2", "开始执行 LangGraph 流程...")
        print("-" * 70)

        node_times = {}
        try:
            async for event in graph.astream(state):
                # LangGraph astream 返回事件
                for node_name, node_state in event.items():
                    if node_name == "__end__":
                        continue
                    elapsed = time.time() - self.start_time
                    node_times[node_name] = elapsed
                    self._log("NODE", f"{node_name} 完成 @ {elapsed:.1f}s")

                    # 记录执行日志
                    logs = node_state.get("execution_log", [])
                    for log in logs:
                        agent = log.get("agent", "?")
                        status = log.get("status", "?")
                        extra = {k: v for k, v in log.items() if k not in ["agent", "status"]}
                        self._log("NODE", f"  -> {agent}: {status} {extra}")

                    # 记录错误
                    errors = node_state.get("errors", [])
                    for err in errors:
                        self._log("NODE", f"  -> ERROR: {err}")

        except Exception as e:
            self._log("PHASE-2", f"LangGraph 执行异常: {e}")
            import traceback
            traceback.print_exc()

        print("-" * 70)

        # Phase 3: 验证结果
        self._log("PHASE-3", "验证运行后表状态...")
        for table in ["热帖库", "选题库", "内容资产库", "Agent协作日志"]:
            self.records_after[table] = self._snapshot(table)
            before_count = self.records_before[table]["count"]
            after_count = self.records_after[table]["count"]
            delta = after_count - before_count
            self._log("PHASE-3", f"  {table}: {before_count} -> {after_count} (新增 {delta})")
            for sample in self.records_after[table].get("sample", []):
                self._log("PHASE-3", f"    样本: {sample}")

        # Phase 4: 详细验证
        self._log("PHASE-4", "详细验证...")
        checks = []

        # 4.1 热帖库应该有数据
        hot_count = self.records_after["热帖库"]["count"]
        hot_ok = hot_count > 0
        checks.append(("热帖库有数据", hot_ok, f"{hot_count} 条"))

        # 4.2 选题库应该有数据
        topic_count = self.records_after["选题库"]["count"]
        topic_ok = topic_count > 0
        checks.append(("选题库有数据", topic_ok, f"{topic_count} 条"))

        # 4.3 查找最新选题和内容资产
        topics = self.storage.query("选题库", limit=5)
        assets = self.storage.query("内容资产库", limit=5)

        if topics:
            latest_topic = topics[0].data
            topic_status = latest_topic.get("选题状态", "N/A")
            topic_title = latest_topic.get("选题标题", "N/A")
            asset_id = latest_topic.get("关联资产ID", "")
            checks.append(("选题有标题", bool(topic_title), topic_title[:40]))
            checks.append(("选题有关联资产", bool(asset_id), asset_id))
            checks.append(("选题状态", True, topic_status))

            # 检查关联资产
            if asset_id:
                asset = self.storage.get_by_id("内容资产库", asset_id)
                if asset:
                    ad = asset.data
                    text_status = ad.get("文案状态", "N/A")
                    image_status = ad.get("配图状态", "N/A")
                    video_status = ad.get("视频状态", "N/A")
                    text_doc = ad.get("文案文档链接", "")
                    image_doc = ad.get("图片提示词文档链接", "")
                    video_doc = ad.get("视频脚本文档链接", "")

                    checks.append(("文案状态", text_status == "已完成", text_status))
                    checks.append(("配图状态", image_status == "已完成", image_status))
                    checks.append(("视频状态", video_status == "已完成", video_status))
                    checks.append(("文案文档链接", bool(text_doc), str(text_doc)[:60]))
                    checks.append(("配图文档链接", bool(image_doc), str(image_doc)[:60]))
                    checks.append(("视频文档链接", bool(video_doc), str(video_doc)[:60]))
                else:
                    checks.append(("关联资产存在", False, f"asset_id={asset_id} not found"))

        # 4.4 Agent协作日志
        logs = self.storage.query("Agent协作日志", limit=20)
        agent_names = set()
        for log in logs:
            name = log.data.get("Agent花名", "")
            if name:
                agent_names.add(name)
        checks.append(("Agent协作日志", len(logs) > 0, f"{len(logs)} 条, 涉及 {agent_names}"))

        # 打印验证结果
        print()
        print("=" * 70)
        print("验证结果汇总")
        print("=" * 70)
        all_pass = True
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            if not ok:
                all_pass = False
            print(f"  [{status}] {name}: {detail}")

        total_time = time.time() - self.start_time
        print()
        print(f"总耗时: {total_time:.1f}s ({total_time/60:.1f}min)")
        print(f"节点执行时间:")
        for node, t in sorted(node_times.items(), key=lambda x: x[1]):
            print(f"  {node}: {t:.1f}s")

        print("=" * 70)
        if all_pass:
            print("全部通过!")
        else:
            print("部分检查未通过，请查看详情")
        print("=" * 70)

        return all_pass


async def main():
    verifier = E2EVerifier()
    success = await verifier.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
