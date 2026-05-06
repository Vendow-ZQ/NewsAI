"""小数 Analyst -- 数据分析师 Agent。

小数是NewsAI的数据分析师，负责：
1. 读取选题库状态="已发布"的选题（发布后24小时）
2. Mock或读取真实平台数据（阅读量/点赞/评论等）
3. 用LLM分析数据，评估选题成败
4. 写入数据库表（DATA）
5. 生成月度经验总结
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any

from core.agents.base import BaseAgent
from core.storage.id_generator import IDGenerator
from core.utils.feishu_base import FeishuBaseManager
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


class AnalystAgent(BaseAgent):
    """小数 Analyst - 数据分析师。

    负责追踪内容表现，分析数据，沉淀经验。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小数", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取已发布选题。

        从"选题库"表中读取状态为"已发布"且发布时间超过24小时的选题。
        """
        try:
            from core.storage.interface import QueryFilter
            # 计算24小时前的时间
            yesterday = (datetime.now() - timedelta(hours=24)).isoformat()

            filters = [
                QueryFilter(field="状态", operator="eq", value="已发布"),
                QueryFilter(field="发布完成时间", operator="lt", value=yesterday)
            ]
            topics = self.storage.query("选题库", filters=filters, limit=100)

            # 过滤掉已经分析过的选题
            unanalyzed_topics = []
            for topic in topics:
                data_id = topic.data.get("数据回流ID", "")
                if not data_id:
                    unanalyzed_topics.append(topic.data)

            return {"topics": unanalyzed_topics}
        except Exception as e:
            print(f"[小数] 读取选题库失败: {e}")
            return {"topics": []}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """读取平台数据。

        从mock或真实API读取平台数据。
        """
        topics = upstream_data.get("topics", [])
        platform_data = []

        for topic in topics:
            topic_id = topic.get("id", "")
            topic_title = topic.get("选题标题", "")

            # 尝试从mock数据读取
            mock_data = self._load_mock_analytics(topic_id)
            if mock_data:
                platform_data.append({
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "predicted_hook": topic.get("预估爆点", ""),
                    "data": mock_data
                })
            else:
                # 生成模拟数据
                mock_data = self._generate_mock_data(topic_title)
                platform_data.append({
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "predicted_hook": topic.get("预估爆点", ""),
                    "data": mock_data
                })

        return {"platform_data": platform_data}

    def _load_mock_analytics(self, topic_id: str) -> dict:
        """从mock文件加载分析数据。"""
        try:
            import os
            mock_file = os.path.join("mock_data", "analytics_mock.json")
            with open(mock_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("选题 ID") == topic_id:
                        return item
            return None
        except Exception as e:
            print(f"[小数] 加载mock数据失败: {e}")
            return None

    def _generate_mock_data(self, topic_title: str) -> dict:
        """生成模拟数据。"""
        # 根据标题长度和关键词简单模拟不同表现
        base_score = random.uniform(0.3, 0.9)

        return {
            "选题标题": topic_title,
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
            "B站_播放量": int(random.uniform(3000, 800000)),
            "B站_点赞数": int(random.uniform(150, 50000)),
            "B站_投币数": int(random.uniform(30, 10000)),
            "综合评分": round(base_score, 2),
            "爆点验证": random.choice(["验证成功", "部分验证", "未爆"])
        }

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM分析数据。

        对每条选题的平台数据，使用LLM分析表现并生成建议。
        """
        platform_data = tool_results.get("platform_data", [])
        analyses = []

        for item in platform_data:
            prompt = self._build_analysis_prompt(item)
            try:
                response = self.llm.invoke(prompt)
                analysis = self._parse_llm_response(response)
                analyses.append({
                    "topic_id": item["topic_id"],
                    "topic_title": item["topic_title"],
                    "analysis": analysis,
                    "raw_data": item["data"]
                })
            except Exception as e:
                print(f"[小数] LLM分析失败: {e}")
                analyses.append({
                    "topic_id": item["topic_id"],
                    "topic_title": item["topic_title"],
                    "analysis": self._fallback_analysis(item),
                    "raw_data": item["data"]
                })

        # 检查是否需要生成月度总结
        monthly_summary = None
        if context.get("generate_monthly_summary", False):
            monthly_summary = self._generate_monthly_summary(analyses)

        return {
            "analyses": analyses,
            "monthly_summary": monthly_summary,
            "count": len(analyses)
        }

    def _build_analysis_prompt(self, item: dict) -> str:
        """构建数据分析提示词。"""
        data = item["data"]
        return f"""你是【小数 Analyst】，分析内容发布数据。

选题信息：
标题：{item["topic_title"]}
预估爆点：{item.get("predicted_hook", "待分析")}
实际爆点：待分析

平台数据：
公众号：阅读量{data.get("公众号_阅读量", 0)}, 点赞{data.get("公众号_点赞数", 0)}, 在看{data.get("公众号_在看数", 0)}
小红书：阅读量{data.get("小红书_阅读量", 0)}, 点赞{data.get("小红书_点赞数", 0)}, 收藏{data.get("小红书_收藏数", 0)}, 评论{data.get("小红书_评论数", 0)}
抖音：播放量{data.get("抖音_播放量", 0)}, 点赞{data.get("抖音_点赞数", 0)}, 评论{data.get("抖音_评论数", 0)}
B站：播放量{data.get("B站_播放量", 0)}, 点赞{data.get("B站_点赞数", 0)}, 投币{data.get("B站_投币数", 0)}

请分析：
1. 综合评分（0-1）
2. 爆点验证（验证成功/部分验证/未爆）
3. 各平台表现分析
4. 成功/失败原因
5. 给小编的下个选题建议

返回JSON：
{{
  "综合评分": 0.85,
  "爆点验证": "验证成功",
  "平台表现": {{
    "最佳平台": "抖音",
    "最差平台": "公众号",
    "分析": "为什么..."
  }},
  "成败分析": "...",
  "选题建议": ["建议1", "建议2"]
}}
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
            print(f"[小数] 解析LLM响应失败: {e}")
            return {}

    def _fallback_analysis(self, item: dict) -> dict:
        """备用分析结果。"""
        data = item["data"]
        score = data.get("综合评分", 0.5)

        if score >= 0.8:
            validation = "验证成功"
        elif score >= 0.5:
            validation = "部分验证"
        else:
            validation = "未爆"

        return {
            "综合评分": score,
            "爆点验证": validation,
            "平台表现": {
                "最佳平台": "待分析",
                "最差平台": "待分析",
                "分析": "数据待进一步分析"
            },
            "成败分析": "基于数据的自动分析",
            "选题建议": ["建议关注热门话题", "建议优化标题吸引力"]
        }

    def _generate_monthly_summary(self, analyses: list) -> dict:
        """生成月度经验总结。"""
        if not analyses:
            return None

        # 统计数据
        total = len(analyses)
        success_count = sum(1 for a in analyses if a["analysis"].get("爆点验证") == "验证成功")
        partial_count = sum(1 for a in analyses if a["analysis"].get("爆点验证") == "部分验证")
        fail_count = total - success_count - partial_count

        success_rate = round(success_count / total * 100, 1) if total > 0 else 0
        avg_score = sum(a["analysis"].get("综合评分", 0) for a in analyses) / total if total > 0 else 0

        prompt = f"""分析过去30天所有发布内容，生成经验文档。

数据汇总：
- 总发布数：{total}
- 爆点验证率：{success_rate}%
- 平均综合评分：{avg_score:.2f}
- 验证成功：{success_count}条
- 部分验证：{partial_count}条
- 未爆：{fail_count}条

请生成月度复盘报告（Markdown格式）：
- TL;DR关键发现
- 数据汇总表格
- 深度洞察（3-5条）
- 给小编的下月选题建议（5-10条）

返回JSON格式：
{{
  "tldr": "关键发现摘要",
  "data_table": "表格内容",
  "insights": ["洞察1", "洞察2", ...],
  "suggestions": ["建议1", "建议2", ...]
}}
"""

        try:
            response = self.llm.invoke(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"[小数] 生成月度总结失败: {e}")
            return {
                "tldr": f"本月发布{total}条内容，验证成功率{success_rate}%",
                "data_table": f"总发布数: {total}, 成功率: {success_rate}%",
                "insights": ["基于数据的自动分析"],
                "suggestions": ["建议持续优化选题策略"]
            }

    def _write_storage(self, context: dict, result: dict):
        """写入DATA表并创建经验总结云文档。

        将分析结果写入"数据库"表，创建/追加经验总结到飞书云文档。
        """
        analyses = result.get("analyses", [])
        doc_storage = FeishuDocStorage()
        period = datetime.now().strftime("%Y%m")
        period_cn = datetime.now().strftime("%Y年%m月")

        for analysis in analyses:
            raw_data = analysis["raw_data"]
            llm_analysis = analysis["analysis"]

            business_id = IDGenerator.generate("DATA")
            topic_title = analysis["topic_title"]
            experience_content = llm_analysis.get("成败分析", "")
            suggestions = llm_analysis.get("选题建议", [])

            # 构建经验总结文档（Markdown格式）
            experience_doc = self._format_experience_document(
                period_cn, topic_title, experience_content, suggestions, raw_data
            )

            try:
                record_data = {
                    "id": business_id,
                    "选题ID": analysis["topic_id"],
                    "选题标题": topic_title,
                    "公众号_阅读量": raw_data.get("公众号_阅读量", 0),
                    "公众号_点赞数": raw_data.get("公众号_点赞数", 0),
                    "公众号_在看数": raw_data.get("公众号_在看数", 0),
                    "小红书_阅读量": raw_data.get("小红书_阅读量", 0),
                    "小红书_点赞数": raw_data.get("小红书_点赞数", 0),
                    "小红书_收藏数": raw_data.get("小红书_收藏数", 0),
                    "小红书_评论数": raw_data.get("小红书_评论数", 0),
                    "抖音_播放量": raw_data.get("抖音_播放量", 0),
                    "抖音_点赞数": raw_data.get("抖音_点赞数", 0),
                    "抖音_评论数": raw_data.get("抖音_评论数", 0),
                    "B站_播放量": raw_data.get("B站_播放量", 0),
                    "B站_点赞数": raw_data.get("B站_点赞数", 0),
                    "B站_投币数": raw_data.get("B站_投币数", 0),
                    "综合评分": llm_analysis.get("综合评分", 0.5),
                    "爆点验证": llm_analysis.get("爆点验证", "未爆"),
                    "数据采集时间": FeishuBaseManager.convert_datetime_to_timestamp(datetime.now()),
                    "数据状态": "已迭代分析",
                }

                self.storage.create("数据库", record_data)

                # 创建/追加经验总结云文档
                existing = self.storage.get_by_id("数据库", business_id)
                existing_url = existing.data.get("经验文档链接", "") if existing else ""

                if existing_url:
                    # Handle URL field format - could be dict or string
                    url_str = existing_url.get('link', '') if isinstance(existing_url, dict) else existing_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                else:
                    doc_id = doc_storage.create_experience_doc(period, topic_title)

                doc_storage.append_section(doc_id, experience_doc)

                # 设置权限（组织内可查看）
                doc_storage.set_permissions(doc_id, share_type="tenant_readable")
                doc_url = doc_storage.get_share_url(doc_id)

                print(f"[小数] 创建数据分析: {topic_title[:30]}...")
                print(f"[小数] 经验总结文档: {doc_url}")

                # 更新数据库的经验文档链接
                self.storage.update("数据库", business_id, {"经验文档链接": doc_url})

                # 更新选题库的数据回流ID
                self.storage.update(
                    "选题库",
                    record_id=analysis["topic_id"],
                    data={"数据回流ID": business_id}
                )
            except Exception as e:
                print(f"[小数] 写入数据库失败: {e}")

    def _format_experience_document(self, period: str, topic_title: str,
                                     analysis: str, suggestions: list, raw_data: dict) -> str:
        """格式化经验总结为Markdown文档。"""
        doc = f"""# {period} AI内容复盘

## 选题：{topic_title}

### 成败分析
{analysis}

### 选题建议
"""
        for suggestion in suggestions:
            doc += f"- {suggestion}\n"

        doc += f"""
### 平台数据
- 公众号：阅读量{raw_data.get('公众号_阅读量', 0)}, 点赞{raw_data.get('公众号_点赞数', 0)}
- 小红书：阅读量{raw_data.get('小红书_阅读量', 0)}, 点赞{raw_data.get('小红书_点赞数', 0)}
- 抖音：播放量{raw_data.get('抖音_播放量', 0)}, 点赞{raw_data.get('抖音_点赞数', 0)}
- B站：播放量{raw_data.get('B站_播放量', 0)}, 点赞{raw_data.get('B站_点赞数', 0)}

---
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return doc

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小数] 完成：分析 {count} 条选题数据")
        super()._log_work(context, result)


# 保持向后兼容的别名
Analyst = AnalystAgent
