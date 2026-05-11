"""小编 TopicCurator - 选题策划 Agent (EMP-002)。

v3.0 改造：
- 一次产 3 条候选（v2 只产 1 条）
- 自动选优先级最高的设为"已选中"
- 创建 ASSET 关联记录
- 修复 KOC 注入
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class TopicCuratorAgent(BaseAgent):
    """小编 EMP-002 · 选题总编"""

    name = "小编"
    english_name = "TopicCurator"
    emoji = "📋"

    SYSTEM_PROMPT = """\
<role>
你是「小编 TopicCurator」，NewsAI 编辑部的选题总编，决策组 leader。
你直接对 KOC 负责。
你的工作是：从全部 21 条热帖中筛选 + 3 关筛查 + 多角度爆点拆解，
最终输出 3 条最优候选选题。
</role>

<workflow>
1. 读 <input> 中的全部 21 条热帖（已经过小哨打分）
2. 在 <thinking> 里：
   - 整体扫描：哪些热帖通过 3 关筛查（领域 / 禁区 / 爆点）
   - 从通过的候选里选出最优 3 条
   - 多角度爆点拆解（情绪/知识增量/身份代入/反差/时效 5 维度）
   - 对每条候选打"推荐优先级"（1-10）
3. 在 <answer> 输出 3 条候选选题
</workflow>

<output_format>
先在 <thinking>...</thinking> 写整体筛查 + 3 条候选的判断（≤500字），
然后 <answer>{3 条候选 JSON}</answer>。
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC 人设 + 全部 21 条热帖"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            if not koc_record:
                raise RuntimeError("KOC-001 不存在")
            koc = parse_koc_data(koc_record.data)

            # v3 改造：读全部 21 条热帖（v2 只读 8 条）
            trends = self.storage.query("热帖库", limit=50)
            trends_data = [t.data for t in trends]

            print(f"[小编] 读取热帖库: {len(trends_data)} 条")
            return {"koc": koc, "trends": trends_data}
        except Exception as e:
            print(f"[小编] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小编不需要外部工具"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 一次返回 3 条候选"""
        koc = upstream_data["koc"]
        trends = upstream_data["trends"]

        # 准备输入
        trends_for_llm = [
            {
                "id": t.get("id", ""),
                "标题": t.get("标题", ""),
                "信源平台": t.get("信源平台", ""),
                "原文摘要": t.get("原文摘要", "")[:200],
                "主题标签": t.get("主题标签", []),
                "小哨热度评分": t.get("热度评分", 0.5),
                "小哨内容质量": t.get("内容质量", "中"),
            }
            for t in trends
        ]

        koc_block = render_koc_block(koc, mode="curation")
        user_content = self._build_user_prompt(koc_block, trends_for_llm)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        # v3 校验：必须有 3 条候选
        candidates = answer.get("candidates", [])
        if len(candidates) != 3:
            raise RuntimeError(
                f"小编必须输出 3 条候选，实际输出 {len(candidates)} 条"
            )

        return {"candidates": candidates}

    def _build_user_prompt(self, koc_block: str, trends: list) -> str:
        """构建用户 prompt"""
        trends_json = json.dumps(trends, ensure_ascii=False, indent=2)

        return f"""\
{koc_block}

<input>
今日热帖池（{len(trends)} 条，已经过小哨初步评分）：

{trends_json}
</input>

<rules>
【3 关筛查标准】

第 1 关 · 领域白名单
- 看 KOC.领域 字段，不在范围一律拒绝

第 2 关 · 禁区话题
- 触碰任意一条 KOC 禁区直接拒绝
- 重点警惕"焦虑制造"型话题

第 3 关 · 爆点可挖掘性
- 不是"这个新闻火"，而是"我能从什么具体角度切"
- 如果只能"翻译原文" → 拒绝

【5 维度爆点拆解（必须在 thinking 里展开）】

每条候选必须评估 5 个维度：
- 情绪钩子（兴奋/反差/共鸣，焦虑必须 0 或负值）
- 知识增量（高/中/低）
- 身份代入（KOC 受众能否代入？）
- 反差（有反预期的点吗？）
- 时效（24h/1 周/更久）

【选题输出约束】

每条候选必须包含：
- 选题标题：10-25 字，前 8 字必有钩子
- 选题角度：「我作为...从...切入...目标是让...」句式
- 预估爆点：说传播心理，不说"信息有价值"
- 预估受众：一句话
- 钩子类型：从「数字/反差/提问/身份代入/时效」选 1
- 推荐优先级：1-10

【输出 3 条候选的规则】
- 优先级由高到低排列
- 至少 1 条优先级 ≥ 8（必须有真"爆款料"）
- 3 条选题角度不重复（多样性）
- 关联热帖_ids 字段必须填入对应 TREND ID
</rules>

<self_check>
输出前确认：
□ candidates 数组长度 = 3
□ 优先级由高到低排列
□ 至少 1 条优先级 ≥ 8
□ 3 条角度不重复
□ 每条标题前 8 字真有钩子
□ 每条选题角度用「我作为...从...切入...」句式
□ 预估爆点说传播心理，不说"信息有价值"
□ 关联热帖_ids 是 TREND-xxx-xxx 格式
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """v3 改造：写 3 条 TOPIC + 自动选最优 + 创建 ASSET"""
        candidates = result["candidates"]

        # 1. 写 3 条选题（状态="待选择"）
        topic_ids = []
        for cand in candidates:
            topic_id = IDGenerator.generate("TOPIC")
            record = {
                "id": topic_id,
                "选题标题": cand["选题标题"],
                "选题角度": cand["选题角度"],
                "预估爆点": cand["预估爆点"],
                "预估受众": cand["预估受众"],
                "钩子类型": cand["钩子类型"],
                "推荐优先级": cand["推荐优先级"],
                "关联热帖IDs": json.dumps(cand.get("关联热帖_ids", []), ensure_ascii=False),
                "KOC人设ID": "KOC-001",
                "选题状态": "待选择",
                "创建时间": current_timestamp_ms(),
                "创建者Agent": "小编 TopicCurator",
            }
            try:
                self.storage.create("选题库", record)
                topic_ids.append((topic_id, cand["推荐优先级"]))
                print(f"[小编] 创建选题: {cand['选题标题'][:30]}... (优先级:{cand['推荐优先级']})")
            except Exception as e:
                print(f"[小编] 写入选题库失败: {e}")

        # 2. 自动选优先级最高的设为"已选中"
        topic_ids.sort(key=lambda x: x[1], reverse=True)
        best_topic_id = topic_ids[0][0]

        # 3. 创建对应的 ASSET 记录
        asset_id = IDGenerator.generate("ASSET")
        best_topic_record = self.storage.get_by_id("选题库", best_topic_id)
        best_topic_title = best_topic_record.data.get("选题标题", "") if best_topic_record else ""

        try:
            self.storage.create("内容资产库", {
                "id": asset_id,
                "选题ID": best_topic_id,
                "选题标题": best_topic_title,
                "文案状态": "未开始",
                "配图状态": "未开始",
                "视频状态": "未开始",
                "审改状态": "未开始",
                "分发状态": "未开始",
                "审改轮次": 0,
            })
            print(f"[小编] 创建 ASSET: {asset_id}")
        except Exception as e:
            print(f"[小编] 创建 ASSET 失败: {e}")

        # 4. 更新 TOPIC.选题状态 = "已选中" + 关联资产 ID
        try:
            self.storage.update("选题库", best_topic_id, {
                "选题状态": "已选中",
                "关联资产ID": asset_id,
                "选定时间": current_timestamp_ms(),
            })
            print(f"[小编] 最优选题已选中: {best_topic_id} → ASSET {asset_id}")
        except Exception as e:
            print(f"[小编] 更新选题状态失败: {e}")

        result["all_topic_ids"] = [t[0] for t in topic_ids]
        result["selected_topic_id"] = best_topic_id
        result["asset_id"] = asset_id
        print(f"[小编] 完成: 生成 {len(topic_ids)} 条选题，选中 {best_topic_id}")


TopicCurator = TopicCuratorAgent
