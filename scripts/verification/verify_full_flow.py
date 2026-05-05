#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NewsAI Full Flow Verification Script"""

import sys
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()


class MockLLM:
    """Mock LLM that returns preset responses"""

    # Use class variables to avoid encoding issues
    KEY_TOPIC = "是否适合"  # 是否适合
    KEY_WECHAT = "公众号"  # 公众号
    KEY_XIAOHONGSHU = "小红书"  # 小红书
    KEY_IMAGE = "配图方案"  # 配图方案
    KEY_SCRIPT = "脚本"  # 脚本
    KEY_REVIEW = "审查结论"  # 审查结论
    KEY_DISTRIBUTE = "分发策略"  # 分发策略
    KEY_ANALYSIS = "综合评分"  # 综合评分
    KEY_HEAT = "热度评分"  # 热度评分

    def invoke(self, prompt: str) -> str:
        p = prompt

        # TopicCurator - topic selection (是否适合)
        if self.KEY_TOPIC in p:
            return '{"是否适合": true, "选题标题": "Test", "选题角度": "Angle", "预估爆点": "Hook", "预估受众": "Audience", "推荐优先级": 9}'

        # ContentWriter - 4 platform content (公众号/小红书)
        if self.KEY_WECHAT in p and self.KEY_XIAOHONGSHU in p:
            return '{"公众号": {"标题": "Test"}, "小红书": {"标题": "Test"}, "抖音": {"文案": "Test"}, "B站": {"标题": "Test"}}'

        # VisualDesigner - image design (配图方案)
        if self.KEY_IMAGE in p:
            return '{"配图方案": [{"配图编号": "1"}], "视觉风格": "Tech"}'

        # ScriptWriter - video script (脚本)
        if self.KEY_SCRIPT in p:
            return '{"抖音版": {}, "B站版": {}}'

        # Reviewer - content review (审查结论)
        if self.KEY_REVIEW in p:
            return '{"审查结论": "通过", "严重度": "低", "发现的问题": []}'

        # Distributor - distribution plan (分发策略)
        if self.KEY_DISTRIBUTE in p:
            return '{"分发策略总结": "Test", "平台分发计划": []}'

        # Analyst - data analysis (综合评分)
        if self.KEY_ANALYSIS in p:
            return '{"综合评分": 0.82, "爆点验证": "success", "平台表现": {}}'

        # TrendScout - heat score (热度评分)
        return '{"热度评分": 0.85, "内容质量": "high", "主题标签": ["AI"]}'


class MockStorage:
    """In-memory storage for testing"""

    def __init__(self):
        self.tables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.id_counters: Dict[str, int] = {}

    def _ensure_table(self, table: str):
        if table not in self.tables:
            self.tables[table] = {}
            self.id_counters[table] = 0

    def _generate_id(self, table: str) -> str:
        prefix_map = {
            "热帖库": "TREND", "选题库": "TOPIC", "数据库": "DATA",
            "KOC人设": "KOC", "信源配置": "SOURCE", "Agent协作日志": "LOG"
        }
        prefix = prefix_map.get(table, "REC")
        self.id_counters[table] += 1
        today = datetime.now().strftime("%Y%m%d")
        return f"{prefix}-{today}-{self.id_counters[table]:03d}"

    def create(self, table: str, data: Dict[str, Any], record_id: str = None) -> str:
        self._ensure_table(table)
        if record_id is None:
            record_id = data.get("id") or self._generate_id(table)
        data["id"] = record_id
        self.tables[table][record_id] = data
        return record_id

    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        self._ensure_table(table)
        if record_id in self.tables[table]:
            self.tables[table][record_id].update(data)
            return True
        return False

    def query(self, table: str, filters: List = None, limit: int = 100, order_by: str = None):
        from core.storage.interface import StorageRecord
        self._ensure_table(table)
        results = []
        for record_id, data in self.tables[table].items():
            if filters:
                match = True
                for f in filters:
                    field_value = data.get(f.field)
                    if f.operator == "eq":
                        match = field_value == f.value
                    elif f.operator == "in":
                        match = field_value in f.value if isinstance(f.value, (list, tuple)) else False
                    if not match:
                        break
                if not match:
                    continue
            results.append(StorageRecord(id=record_id, table=table, data=data))
        return results[:limit]

    def get_by_id(self, table: str, record_id: str):
        from core.storage.interface import StorageRecord
        self._ensure_table(table)
        if record_id in self.tables[table]:
            return StorageRecord(id=record_id, table=table, data=self.tables[table][record_id])
        return None

    def get_all(self, table: str) -> Dict[str, Any]:
        self._ensure_table(table)
        return dict(self.tables[table])

    def count(self, table: str) -> int:
        self._ensure_table(table)
        return len(self.tables[table])


def print_sep(title: str = None):
    if title:
        print(f"\n{'='*60}\n  {title}\n{'='*60}")
    else:
        print(f"{'='*60}")


def print_ok(name: str, msg: str = ""):
    print(f"  [OK] {name}: {msg}")


def print_err(name: str, msg: str = ""):
    print(f"  [ERR] {name}: {msg}")


class Verifier:
    def __init__(self):
        print_sep("NewsAI Full Flow Verification")
        self.storage = MockStorage()
        print_ok("Storage", "MockStorage")
        self.llm = MockLLM()
        print_ok("LLM", "MockLLM")
        self._init_agents()
        self._init_data()
        self.results = {"agents": {}, "records": {}, "errors": []}

    def _init_agents(self):
        from core.agents.trend_scout import TrendScoutAgent
        from core.agents.topic_curator import TopicCuratorAgent
        from core.agents.content_writer import ContentWriterAgent
        from core.agents.visual_designer import VisualDesignerAgent
        from core.agents.script_writer import ScriptWriterAgent
        from core.agents.reviewer import ReviewerAgent
        from core.agents.distributor import DistributorAgent
        from core.agents.analyst import AnalystAgent

        self.agents = {
            "TrendScout": TrendScoutAgent(self.storage, self.llm),
            "TopicCurator": TopicCuratorAgent(self.storage, self.llm),
            "ContentWriter": ContentWriterAgent(self.storage, self.llm),
            "VisualDesigner": VisualDesignerAgent(self.storage, self.llm),
            "ScriptWriter": ScriptWriterAgent(self.storage, self.llm),
            "Reviewer": ReviewerAgent(self.storage, self.llm),
            "Distributor": DistributorAgent(self.storage, self.llm),
            "Analyst": AnalystAgent(self.storage, self.llm),
        }
        print_ok("Agents", f"{len(self.agents)} initialized")

    def _init_data(self):
        # KOC - use Chinese table names
        self.storage.create("KOC人设", {
            "id": "KOC-001", "账号名": "TestKOC", "语气": "Playful", "领域": ["AI"]
        }, "KOC-001")
        # Sources - use Chinese table names
        self.storage.create("信源配置", {
            "id": "SOURCE-001", "平台": "hackernews", "是否启用": True, "每次抓取上限": 5
        }, "SOURCE-001")
        print_ok("Data", "KOC and sources created")

    def step1(self) -> bool:
        print_sep("Step 1: TrendScout")
        try:
            # Create mock trends
            for i in range(3):
                self.storage.create("热帖库", {
                    "id": f"TREND-{i}", "biao_ti": f"News {i}", "yuan_wen_zhai_yao": f"Summary {i}",
                    "xin_yuan_ping_tai": "hn", "re_du_ping_fen": 0.8, "状态": "pending",
                    "zhua_qu_shi_jian": datetime.now().isoformat()
                }, f"TREND-{i}")

            result = self.agents["TrendScout"].execute({"koc_id": "KOC-001"})
            count = self.storage.count("热帖库")
            print_ok("TrendScout", f"{count} records")
            self.results["agents"]["TrendScout"] = {"success": True, "count": count}
            return True
        except Exception as e:
            print_err("TrendScout", str(e))
            self.results["errors"].append({"agent": "TrendScout", "error": str(e)})
            return False

    def step2(self) -> bool:
        print_sep("Step 2: TopicCurator")
        try:
            koc = self.storage.get_by_id("KOC人设", "KOC-001")
            result = self.agents["TopicCurator"].execute({"koc_id": "KOC-001", "koc": koc.data if koc else {}})
            count = result.get("count", 0)
            print_ok("TopicCurator", f"{count} topics")
            self.results["agents"]["TopicCurator"] = {"success": True, "count": count}
            return count > 0
        except Exception as e:
            print_err("TopicCurator", str(e))
            self.results["errors"].append({"agent": "TopicCurator", "error": str(e)})
            traceback.print_exc()
            return False

    def step3(self) -> bool:
        print_sep("Step 3: Content Production")
        from core.storage.interface import QueryFilter
        # Query for topics with status "已选" (selected)
        topics = self.storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="已选")], limit=1)
        if not topics:
            print_err("ContentProduction", "No topics found")
            return False

        topic_id = topics[0].data.get("id")
        print(f"  Using topic: {topic_id}")

        results = {}
        def run(name, agent, ctx):
            try:
                return (name, True, agent.execute(ctx), None)
            except Exception as e:
                return (name, False, None, str(e))

        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {
                ex.submit(run, "ContentWriter", self.agents["ContentWriter"], {"koc_id": "KOC-001"}): "ContentWriter",
                ex.submit(run, "VisualDesigner", self.agents["VisualDesigner"], {"koc_id": "KOC-001", "topic_id": topic_id}): "VisualDesigner",
                ex.submit(run, "ScriptWriter", self.agents["ScriptWriter"], {"koc_id": "KOC-001", "topic_id": topic_id}): "ScriptWriter",
            }
            for f in futures:
                name, ok, result, err = f.result()
                if ok:
                    print_ok(name, f"Done: {result.get('count', 0)}")
                    results[name] = {"success": True, "count": result.get("count", 0)}
                else:
                    print_err(name, f"Error: {err}")
                    results[name] = {"success": False, "error": err}

        self.results["agents"].update(results)
        return all(r["success"] for r in results.values())

    def step4(self) -> bool:
        print_sep("Step 4: Reviewer")
        try:
            result = self.agents["Reviewer"].execute({"koc_id": "KOC-001"})
            count = len(result.get("review_results", []))
            print_ok("Reviewer", f"{count} reviews")
            self.results["agents"]["Reviewer"] = {"success": True, "count": count}
            return True
        except Exception as e:
            print_err("Reviewer", str(e))
            self.results["errors"].append({"agent": "Reviewer", "error": str(e)})
            return False

    def step5(self) -> bool:
        print_sep("Step 5: Distributor")
        try:
            result = self.agents["Distributor"].execute({"koc_id": "KOC-001"})
            count = len(result.get("distribution_results", []))
            print_ok("Distributor", f"{count} plans")
            self.results["agents"]["Distributor"] = {"success": True, "count": count}
            return True
        except Exception as e:
            print_err("Distributor", str(e))
            self.results["errors"].append({"agent": "Distributor", "error": str(e)})
            return False

    def step6(self) -> bool:
        print_sep("Step 6: Analyst")
        try:
            from core.storage.interface import QueryFilter
            topics = self.storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="待发布")], limit=10)
            yesterday = int((datetime.now() - timedelta(hours=25)).timestamp() * 1000)
            for t in topics:
                self.storage.update("选题库", t.data.get("id"), {"状态": "published", "fa_bu_wan_cheng_shi_jian": yesterday})

            result = self.agents["Analyst"].execute({"koc_id": "KOC-001", "generate_monthly_summary": True})
            count = len(result.get("analyses", []))
            has_summary = result.get("monthly_summary") is not None
            print_ok("Analyst", f"{count} analyses, summary: {has_summary}")
            self.results["agents"]["Analyst"] = {"success": True, "count": count, "has_summary": has_summary}
            return True
        except Exception as e:
            print_err("Analyst", str(e))
            self.results["errors"].append({"agent": "Analyst", "error": str(e)})
            return False

    def verify(self):
        print_sep("Verification")
        v = {
            "热帖库": {"exists": False, "count": 0},
            "选题库": {"exists": False, "count": 0, "has_post": False, "has_script": False, "has_review": False},
            "数据库": {"exists": False, "count": 0, "has_summary": False},
        }

        hot = self.storage.get_all("热帖库")
        v["热帖库"] = {"exists": len(hot) > 0, "count": len(hot)}
        print(f"  Hot posts: {len(hot)}")

        topics = self.storage.get_all("选题库")
        v["选题库"] = {
            "exists": len(topics) > 0, "count": len(topics),
            "has_post": any(t.get("tie_zi_nei_rong") for t in topics.values()),
            "has_script": any(t.get("shi_pin_jiao_ben") for t in topics.values()),
            "has_review": any(t.get("shen_gai_ji_lu") for t in topics.values()),
        }
        print(f"  Topics: {len(topics)}")

        data = self.storage.get_all("数据库")
        v["数据库"] = {"exists": len(data) > 0, "count": len(data), "has_summary": any(d.get("jing_yan_zong_jie") for d in data.values())}
        print(f"  Data: {len(data)}")

        self.results["records"] = v
        return v

    def summary(self) -> bool:
        print_sep("Summary")
        total = len(self.agents)
        success = sum(1 for r in self.results["agents"].values() if r.get("success"))
        print(f"\nAgents: {total} total, {success} success")
        for name, r in self.results["agents"].items():
            print(f"  {'[OK]' if r.get('success') else '[ERR]'} {name}: {r.get('count', 0)}")

        records = self.results.get("records", {})
        print(f"\nRecords:")
        for table, info in records.items():
            print(f"  {'[OK]' if info.get('exists') else '[X]'} {table}: {info.get('count', 0)}")

        t = records.get("选题库", {})
        print(f"\nFields verified:")
        print(f"  Post content: {'[OK]' if t.get('has_post') else '[X]'}")
        print(f"  Video script: {'[OK]' if t.get('has_script') else '[X]'}")
        print(f"  Review record: {'[OK]' if t.get('has_review') else '[X]'}")

        d = records.get("数据库", {})
        print(f"  Experience summary: {'[OK]' if d.get('has_summary') else '[X]'}")

        if self.results["errors"]:
            print(f"\nErrors:")
            for e in self.results["errors"]:
                print(f"  [ERR] {e['agent']}: {e['error']}")

        print_sep()
        passed = (
            success == total and
            records.get("热帖库", {}).get("exists") and
            records.get("选题库", {}).get("exists") and
            t.get("has_post") and t.get("has_script") and t.get("has_review") and
            records.get("数据库", {}).get("exists")
        )
        print("[OK] FULL FLOW VERIFICATION PASSED!" if passed else "[WARN] VERIFICATION PARTIAL")
        print_sep()
        return passed

    def run(self) -> bool:
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        steps = [self.step1, self.step2, self.step3, self.step4, self.step5, self.step6]
        for i, step in enumerate(steps, 1):
            if not step():
                print(f"\n[STOP] Step {i} failed")
                break

        self.verify()
        result = self.summary()
        print(f"\nEnd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return result


def main():
    v = Verifier()
    success = v.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
