"""小数 Analyst - 数据分析 Agent (EMP-009)。

v3.0 改造：
- 读 mock_data/analytics_mock.json（不再 random）
- 按选题优先级匹配档位
"""

import json
import random
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class AnalystAgent(BaseAgent):
    """小数 EMP-009 · 数据分析师"""

    name = "小数"
    english_name = "Analyst"
    emoji = "📊"

    SYSTEM_PROMPT = """\
<role>
你是「小数 Analyst」，NewsAI 编辑部的数据分析师，独立复盘组。
你直接对 KOC 负责。

【你当前在执行：单条数据回流任务】

你的工作是：拿到一条已发布选题的多平台数据，做综合评分 + 爆点验证 + 失败原因分析。
</role>

<workflow>
1. 读 <input>：选题 + 5 平台 mock 数据
2. 在 <thinking> 里：
   - 计算综合评分（按算法权重）
   - 判断爆点验证结果
   - 找最佳/最差平台
   - 如果未爆，分析失败原因
3. 在 <answer> 输出 JSON
</workflow>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读已发布的选题"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"已发布"状态的选题
            topics = self.storage.query("选题库", limit=10)
            published = [t.data for t in topics if t.data.get("选题状态") == "已发布"]
            if not published:
                raise RuntimeError("没有已发布的选题")
            topic = published[0]

            return {"koc": koc, "topic": topic}
        except Exception as e:
            print(f"[小数] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """读 mock 数据按选题预估爆点强度匹配档位"""
        topic = upstream_data["topic"]
        priority = topic.get("推荐优先级", 5)

        # v3 修复 Bug 8：读 mock 文件不 random
        try:
            with open("mock_data/analytics_mock.json", encoding="utf-8") as f:
                mock_pool = json.load(f)
        except Exception as e:
            print(f"[小数] 读取 analytics_mock.json 失败: {e}")
            # fallback: 生成模拟数据
            return {"mock_data": self._generate_fallback_data(priority)}

        # 按选题优先级匹配档位
        if priority >= 8:
            tier = "高表现"
        elif priority >= 5:
            tier = "中表现"
        else:
            tier = "低表现"

        tier_data = mock_pool.get(tier, [])
        if not tier_data:
            # fallback
            return {"mock_data": self._generate_fallback_data(priority)}

        # 从对应档位随机选 1 条（同档位 mock 数据相似）
        mock_data = random.choice(tier_data)
        mock_data["_tier"] = tier

        return {"mock_data": mock_data, "tier": tier}

    def _generate_fallback_data(self, priority: int) -> dict:
        """生成 fallback 模拟数据"""
        base = random.uniform(0.3, 0.9)
        if priority >= 8:
            base = random.uniform(0.7, 0.95)
        elif priority >= 5:
            base = random.uniform(0.4, 0.75)

        return {
            "公众号_阅读量": int(random.uniform(1000, 100000)),
            "公众号_点赞数": int(random.uniform(50, 5000)),
            "公众号_在看数": int(random.uniform(20, 2000)),
            "小红书_阅读量": int(random.uniform(2000, 150000)),
            "小红书_点赞数": int(random.uniform(100, 8000)),
            "小红书_收藏数": int(random.uniform(50, 5000)),
            "小红书_评论数": int(random.uniform(10, 500)),
            "抖音_播放量": int(random.uniform(5000, 2000000)),
            "抖音_点赞数": int(random.uniform(200, 100000)),
            "抖音_评论数": int(random.uniform(50, 3000)),
            "视频号_播放量": int(random.uniform(3000, 100000)),
            "视频号_点赞数": int(random.uniform(100, 5000)),
            "视频号_转发数": int(random.uniform(50, 2000)),
            "B站_播放量": int(random.uniform(3000, 800000)),
            "B站_点赞数": int(random.uniform(150, 50000)),
            "B站_投币数": int(random.uniform(30, 10000)),
            "_tier": "模拟",
        }

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 分析数据"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        mock_data = tool_results["mock_data"]

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="analytics")
        user_content = self._build_user_prompt(koc_block, topic, mock_data)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        return {
            "analysis": answer,
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "mock_data": mock_data,
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, mock_data: dict) -> str:
        """构建用户 prompt"""
        return f"""\
{koc_block}

<input>
任务类型：单条数据回流
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
预估爆点：{topic.get('预估爆点', '')}
预估受众：{topic.get('预估受众', '')}
钩子类型：{topic.get('钩子类型', '')}

【5 平台 mock 数据（来自 analytics_mock.json）】
档位：{mock_data.get('_tier', '未知')}

公众号：阅读={mock_data.get('公众号_阅读量', 0)}，点赞={mock_data.get('公众号_点赞数', 0)}，在看={mock_data.get('公众号_在看数', 0)}
小红书：阅读={mock_data.get('小红书_阅读量', 0)}，点赞={mock_data.get('小红书_点赞数', 0)}，收藏={mock_data.get('小红书_收藏数', 0)}，评论={mock_data.get('小红书_评论数', 0)}
抖音：播放={mock_data.get('抖音_播放量', 0)}，点赞={mock_data.get('抖音_点赞数', 0)}，评论={mock_data.get('抖音_评论数', 0)}
视频号：播放={mock_data.get('视频号_播放量', 0)}，点赞={mock_data.get('视频号_点赞数', 0)}，转发={mock_data.get('视频号_转发数', 0)}
B站：播放={mock_data.get('B站_播放量', 0)}，点赞={mock_data.get('B站_点赞数', 0)}，投币={mock_data.get('B站_投币数', 0)}
</input>

<rules>
【综合评分（0-1）算法】
按 5 平台贡献加权：
- 公众号：0.25
- 小红书：0.20
- 抖音：0.25
- 视频号：0.10
- B站：0.20

【爆点验证】
- "验证成功"：综合评分 ≥ 0.7
- "部分验证"：综合评分 0.4-0.7
- "未爆"：综合评分 < 0.4

【失败原因（未爆时必须分析）】
- 钩子失效：标题/开头不够抓人
- 选题偏离：预估受众与实际不匹配
- 时机不对：错过黄金时段或竞争激烈
- 平台特性：内容不适合该平台调性

【输出 JSON 结构】
{{
  "综合评分": 0.85,
  "爆点验证": "验证成功",
  "平台表现": {{
    "最佳平台": "抖音",
    "最差平台": "公众号",
    "分析": "..."
  }},
  "成败分析": "200-400 字分析",
  "选题建议": ["建议1", "建议2", "建议3"]
}}
</rules>

<self_check>
输出前确认：
□ 综合评分是 0-1 之间的浮点数
□ 爆点验证三选一（验证成功/部分验证/未爆）
□ 平台表现含最佳/最差平台
□ 成败分析 200-400 字
□ 选题建议至少 3 条
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """写 DATA 表 + 更新 TOPIC"""
        analysis = result.get("analysis", {})
        topic_id = result.get("topic_id", "")
        topic_title = result.get("topic_title", "")
        mock_data = result.get("mock_data", {})

        # 生成 DATA ID
        data_id = IDGenerator.generate("DATA")

        try:
            record = {
                "id": data_id,
                "选题ID": topic_id,
                "选题标题": topic_title,
                "公众号_阅读量": mock_data.get("公众号_阅读量", 0),
                "公众号_点赞数": mock_data.get("公众号_点赞数", 0),
                "公众号_在看数": mock_data.get("公众号_在看数", 0),
                "小红书_阅读量": mock_data.get("小红书_阅读量", 0),
                "小红书_点赞数": mock_data.get("小红书_点赞数", 0),
                "小红书_收藏数": mock_data.get("小红书_收藏数", 0),
                "小红书_评论数": mock_data.get("小红书_评论数", 0),
                "抖音_播放量": mock_data.get("抖音_播放量", 0),
                "抖音_点赞数": mock_data.get("抖音_点赞数", 0),
                "抖音_评论数": mock_data.get("抖音_评论数", 0),
                "视频号_播放量": mock_data.get("视频号_播放量", 0),
                "视频号_点赞数": mock_data.get("视频号_点赞数", 0),
                "视频号_转发数": mock_data.get("视频号_转发数", 0),
                "B站_播放量": mock_data.get("B站_播放量", 0),
                "B站_点赞数": mock_data.get("B站_点赞数", 0),
                "B站_投币数": mock_data.get("B站_投币数", 0),
                "综合评分": analysis.get("综合评分", 0.5),
                "爆点验证": analysis.get("爆点验证", "未爆"),
                "数据采集时间": current_timestamp_ms(),
                "数据状态": "已分析",
            }
            self.storage.create("数据库", record)
            print(f"[小数] 创建 DATA 记录: {data_id}")
        except Exception as e:
            print(f"[小数] 写 DATA 表失败: {e}")

        # 更新 TOPIC.数据回流 ID
        if topic_id:
            try:
                self.storage.update("选题库", topic_id, {
                    "数据回流ID": data_id,
                })
                print(f"[小数] TOPIC {topic_id} 数据回流: {data_id}")
            except Exception as e:
                print(f"[小数] 更新 TOPIC 失败: {e}")

        result["data_id"] = data_id


Analyst = AnalystAgent
