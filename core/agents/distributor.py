"""小发 Distributor -- 分发策略 Agent (EMP-008)。
SYSTEM_PROMPT = """
\
<role>
你是「小发 Distributor」，NewsAI 编辑部的分发策略师，治理组成员。
你的工作是：拿到通过审改的终稿后，制定多平台分发计划——
平台×时间×受众×文案变体的组合策略。
</role>

<workflow>
1. 读 <input>：终稿（4 平台版本）+ KOC 分发偏好
2. 在 <thinking> 里规划：
   - 各平台流量黄金时段
   - 错峰发布策略（避免流量分散）
   - 各平台文案是否需要再微调
3. 在 <answer> 输出分发计划 JSON
</workflow>
"""


小发是NewsAI治理组的分发策略师，负责：
1. 读取选题库中状态="待发布"的选题
2. 调用LLM生成分发计划（4平台时间策略）
3. 更新选题库：分发计划JSON字段 + 状态="已发布" + 发布完成时间

分发策略逻辑：
- 基于KOC人设中的平台偏好、发布频率、偏好发布时段
- 生成4平台（公众号、小红书、抖音、B站）的具体分发计划
- 包含发布时间、平台特定优化、发布顺序等
"""

import json
from datetime import datetime, timedelta
from typing import Any

from core.agents.base import BaseAgent


class DistributorAgent(BaseAgent):
    """小发 Distributor - 分发策略师。

    负责制定多平台分发计划，优化发布时间和策略。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小发", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中"待发布"状态的选题。

        从"选题库"表中读取状态为"待发布"的选题，
        并读取KOC人设中的分发偏好。
        """
        try:
            from core.storage.interface import QueryFilter

            # 读取待发布的选题（使用QueryFilter，测试显示它能工作）
            from core.storage.interface import QueryFilter
            filters = [QueryFilter(field="状态", operator="eq", value="待发布")]
            topics = self.storage.query("选题库", filters=filters, limit=10)

            # 获取KOC人设
            koc = self._load_koc(context.get("koc_id", "KOC-001"))

            return {
                "topics": [t.data for t in topics],
                "koc": koc
            }
        except Exception as e:
            print(f"[小发] 读取选题库失败: {e}")
            return {"topics": [], "koc": {}}

    def _load_koc(self, koc_id: str) -> dict:
        """加载KOC人设。"""
        try:
            record = self.storage.get_by_id("KOC人设", koc_id)
            return record.data if record else {}
        except Exception as e:
            print(f"[小发] 加载KOC人设失败: {e}")
            return {}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小发不需要调用外部工具，直接返回空结果。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM生成分发计划。

        对每个选题，基于KOC人设的分发偏好：
        - 分析内容特点和平台适配性
        - 生成4平台的分发时间策略
        - 提供平台特定优化建议
        """
        topics = upstream_data.get("topics", [])
        koc = upstream_data.get("koc", {})

        distribution_results = []
        for topic in topics:
            # 获取帖子文档链接和视频脚本链接（云文档URL）
            post_doc_url = topic.get("帖子文档链接", "")
            script_doc_url = topic.get("视频脚本文档链接", "")

            # 云文档内容不在字段中，使用选题元数据构建分发计划
            posts = {"文档链接": post_doc_url}
            scripts = {"文档链接": script_doc_url}

            # 构建分发计划提示词
            prompt = self._build_distribution_prompt(topic, posts, scripts, koc)

            try:
                response = self.llm.invoke(prompt)
                distribution_plan = self._parse_llm_response(response)

                distribution_results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "distribution_plan": distribution_plan,
                })
            except Exception as e:
                print(f"[小发] LLM生成分发计划失败: {e}")

        return {"distribution_results": distribution_results, "count": len(distribution_results)}

    def _build_distribution_prompt(self, topic: dict, posts: dict, scripts: dict, koc: dict) -> str:
        """构建分发计划提示词。"""
        # 提取KOC分发相关字段
        koc_name = koc.get("账号名", "学AI的刘同学")
        platforms = koc.get("主战场平台", ["公众号", "小红书", "抖音", "B站"])
        post_frequency = koc.get("发布频率", "每周 3 次")
        preferred_time = koc.get("偏好发布时段", ["中 12-13"])
        platform_strategy = koc.get("平台差异化策略", "")
        accounts = koc.get("各平台账号", "")

        # 格式化平台列表
        platform_text = "、".join(platforms) if isinstance(platforms, list) else platforms

        # 格式化帖子内容摘要
        post_summary = ""
        if posts:
            for platform, content in posts.items():
                if content and isinstance(content, str):
                    post_summary += f"\n{platform}: {content[:100]}..."

        return f"""你是【小发 Distributor】，为KOC【{koc_name}】制定分发计划。

KOC主战场平台：{platform_text}
发布频率：{post_frequency}
偏好发布时段：{preferred_time}
各平台账号：
{accounts}

平台差异化策略：
{platform_strategy}

请为以下内容制定分发计划：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}

帖子内容摘要：{post_summary}

请返回JSON格式：
{{
  "分发策略总结": "简要说明整体分发思路",
  "平台分发计划": [
    {{
      "平台": "公众号",
      "发布时间": "2026-05-05 12:00",
      "发布账号": "学AI的刘同学",
      "内容形式": "图文/视频",
      "优化建议": "针对该平台的具体优化建议",
      "预期效果": "预计阅读/互动量"
    }},
    {{
      "平台": "小红书",
      "发布时间": "2026-05-05 12:30",
      "发布账号": "@学AI的刘同学",
      "内容形式": "图文/视频",
      "优化建议": "针对该平台的具体优化建议",
      "预期效果": "预计阅读/互动量"
    }},
    {{
      "平台": "抖音",
      "发布时间": "2026-05-05 19:00",
      "发布账号": "@学AI的刘同学",
      "内容形式": "短视频",
      "优化建议": "针对该平台的具体优化建议",
      "预期效果": "预计播放/互动量"
    }},
    {{
      "平台": "B站",
      "发布时间": "2026-05-05 20:00",
      "发布账号": "学AI的刘同学",
      "内容形式": "视频/专栏",
      "优化建议": "针对该平台的具体优化建议",
      "预期效果": "预计播放/阅读/互动量"
    }}
  ],
  "发布顺序建议": "公众号→小红书→抖音→B站",
  "时间间隔策略": "各平台发布时间错开30分钟，避免流量分散",
  "平台特定优化": {{
    "公众号": "标题优化建议、封面图建议",
    "小红书": "标签建议、封面图建议",
    "抖音": "标题优化建议、标签建议、BGM建议",
    "B站": "分区建议、标签建议、封面图建议"
  }},
  "风险提示": "需要注意的合规或平台规则问题"
}}

分发策略原则：
1. 严格遵循KOC的偏好发布时段
2. 考虑各平台的用户活跃时间
3. 错开发布时间，避免同一时间在多平台同时发布
4. 根据内容特点选择最适合的首发平台
5. 提供具体的平台优化建议（标签、标题、封面等）

注意：
- 发布时间必须是未来时间（从明天开始）
- 考虑工作日和周末的差异
- 避开已知的热点事件时间
- 确保发布频率符合KOC设定
"""

    def _parse_llm_response(self, response: Any) -> dict:
        """解析LLM响应。"""
        try:
            if isinstance(response, str):
                content = response
            elif hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)

            # 尝试从markdown代码块中提取JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"[小发] 解析LLM响应失败: {e}")
            return {
                "分发策略总结": "解析失败，使用默认策略",
                "平台分发计划": [],
                "发布顺序建议": "按默认顺序发布",
                "时间间隔策略": "默认间隔",
                "平台特定优化": {},
                "风险提示": "请人工检查"
            }

    def _write_storage(self, context: dict, result: dict):
        """更新选题库。

        将分发计划写入选题库：
        - 更新分发计划JSON字段
        - 状态改为"已发布"
        - 记录发布完成时间
        """
        distribution_results = result.get("distribution_results", [])

        for dist in distribution_results:
            topic_id = dist.get("topic_id", "")
            plan_data = dist.get("distribution_plan", {})

            # 获取当前时间作为发布完成时间
            publish_time = int(datetime.now().timestamp() * 1000)

            update_data = {
                "分发计划JSON": json.dumps(plan_data, ensure_ascii=False, indent=2),
                "状态": "已发布",
                "发布完成时间": publish_time,
            }

            try:
                self.storage.update("选题库", topic_id, update_data)
                print(f"[小发] 分发计划完成：{dist.get('topic_title', '')[:30]}... "
                      f"状态：已发布")
            except Exception as e:
                print(f"[小发] 更新选题库失败: {e}")

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小发] 完成：制定 {count} 条选题的分发计划")
        super()._log_work(context, result)


# 保持向后兼容的别名
Distributor = DistributorAgent
