"""小数 Analyst - 数据分析 Agent (EMP-009)。

v3.1 改造：
- 从 数据库 表读取真实数据（不再读 mock json）
- 生成经验总结文档 + 数据分析文档
- 沉淀到飞书云文档
"""

import json
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

【你当前在执行：数据复盘分析】

你的工作是：拿到一条选题的多平台真实数据，做深度分析：
1. 数据表现与选题策划/内容质量之间的关联分析
2. 各平台差异原因分析
3. 可沉淀的经验总结
4. 选题策略优化建议
</role>

<workflow>
1. 读 <input>：选题信息 + 多平台真实数据 + 分发内容摘要
2. 在 <thinking> 里分析数据与内容的关系
3. 在 <answer> 输出分析结论
</workflow>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + 最新 DATA 记录 + 关联选题和资产"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 取最新的 DATA 记录（由 mock_data_demo.py 或真实数据生成）
            data_records = self.storage.query("数据库", limit=10)
            if not data_records:
                raise RuntimeError("数据库表中没有数据记录。请先运行 scripts/mock_data_demo.py 生成数据。")

            # 找数据状态为"待分析"或"已分析"的最新记录
            data_record = None
            for r in data_records:
                if r.data.get("数据状态") in ["待分析", "已分析"]:
                    data_record = r.data
                    break
            if not data_record:
                data_record = data_records[0].data

            topic_id = data_record.get("选题ID", "")
            topic = None
            if topic_id:
                topic_rec = self.storage.get_by_id("选题库", topic_id)
                if topic_rec:
                    topic = topic_rec.data

            # 读关联资产（获取分发文档内容用于分析）
            asset = None
            if topic:
                asset_id = topic.get("关联资产ID", "")
                if asset_id:
                    asset_rec = self.storage.get_by_id("内容资产库", asset_id)
                    if asset_rec:
                        asset = asset_rec.data

            return {
                "koc": koc,
                "data": data_record,
                "topic": topic,
                "asset": asset,
            }
        except Exception as e:
            print(f"[小数] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """读取分发文档内容摘要（用于分析数据与内容的关系）"""
        asset = upstream_data.get("asset", {})
        doc_snippets = {}

        # 尝试读取各分发文档的前500字作为摘要
        for field in ["公众号分发文档链接", "小红书分发文档链接", "抖音分发文档链接", "B站分发文档链接"]:
            url = asset.get(field)
            if url:
                try:
                    from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                    doc_storage = FeishuDocStorage()
                    url_str = url.get("link", "") if isinstance(url, dict) else str(url)
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        content = doc_storage.read_doc_content(doc_id) or ""
                        doc_snippets[field.replace("分发文档链接", "")] = content[:500]
                except Exception:
                    pass

        return {"doc_snippets": doc_snippets}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 深度分析"""
        koc = upstream_data["koc"]
        data = upstream_data["data"]
        topic = upstream_data.get("topic", {})
        doc_snippets = tool_results.get("doc_snippets", {})

        koc_block = render_koc_block(koc, mode="analytics")
        user_content = self._build_user_prompt(koc_block, topic, data, doc_snippets)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        if isinstance(answer, str):
            try:
                answer = json.loads(answer)
            except:
                answer = {"综合评分": 0.5, "爆点验证": "未爆", "平台表现": {}, "成败分析": "", "选题建议": []}

        return {
            "analysis": answer,
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "data": data,
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, data: dict, doc_snippets: dict) -> str:
        """构建用户 prompt"""
        docs_text = ""
        for platform, snippet in doc_snippets.items():
            docs_text += f"\n【{platform}分发内容摘要】\n{snippet}\n"

        return f"""\
{koc_block}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}
钩子类型：{topic.get('钩子类型', '')}

【多平台真实数据】
公众号：阅读={data.get('公众号_阅读量', 0)}，点赞={data.get('公众号_点赞数', 0)}，在看={data.get('公众号_在看数', 0)}
小红书：阅读={data.get('小红书_阅读量', 0)}，点赞={data.get('小红书_点赞数', 0)}，收藏={data.get('小红书_收藏数', 0)}，评论={data.get('小红书_评论数', 0)}
抖音：播放={data.get('抖音_播放量', 0)}，点赞={data.get('抖音_点赞数', 0)}，评论={data.get('抖音_评论数', 0)}
视频号：播放={data.get('视频号_播放量', 0)}，点赞={data.get('视频号_点赞数', 0)}，转发={data.get('视频号_转发数', 0)}
B站：播放={data.get('B站_播放量', 0)}，点赞={data.get('B站_点赞数', 0)}，投币={data.get('B站_投币数', 0)}

综合评分：{data.get('综合评分', 0.5)}
爆点验证：{data.get('爆点验证', '未爆')}
{docs_text}
</input>

<rules>
【分析要求】
1. 数据与选题的关联：哪些数据表现印证了选题策划时的判断？哪些偏离了预期？
2. 平台差异分析：为什么某些平台表现好/差？与内容形式、受众画像的关系是什么？
3. 内容质量归因：数据表现与文案、配图、视频脚本质量之间的关联
4. 可沉淀经验：总结出 3-5 条可复用的经验
5. 选题策略优化：基于数据反馈，提出下一期选题的优化建议

【输出 JSON 结构】
{{
  "综合评分": {data.get('综合评分', 0.5)},
  "爆点验证": "{data.get('爆点验证', '未爆')}",
  "平台表现": {{
    "最佳平台": "...",
    "最差平台": "...",
    "分析": "..."
  }},
  "数据与内容关联分析": "300-500字",
  "可沉淀经验": ["经验1", "经验2", "经验3", "经验4", "经验5"],
  "选题策略优化建议": ["建议1", "建议2", "建议3"],
  "经验总结文档标题": "...
}}
</rules>

<self_check>
□ 分析有深度，不是简单复述数据
□ 经验总结具体可复用，不是空话
□ 建议有针对性，与数据表现直接关联
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """生成经验文档 + 数据分析文档，更新 DATA 表"""
        analysis = result.get("analysis", {})
        topic_id = result.get("topic_id", "")
        topic_title = result.get("topic_title", "")
        data_record = result.get("data", {})
        data_id = data_record.get("id", "")

        date_str = datetime.now().strftime("%Y%m%d")

        # 1. 生成经验总结文档
        exp_doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            exp_markdown = self._format_experience_doc(topic_title, analysis)
            exp_doc_id = doc_storage.create_doc(f"[经验] {date_str} {topic_title}")
            doc_storage.append_section(exp_doc_id, exp_markdown)
            doc_storage.set_permissions(exp_doc_id, share_type="tenant_readable")
            exp_doc_url = doc_storage.get_share_url(exp_doc_id)
            print(f"[小数] 创建经验文档: {topic_title[:30]}...")
        except Exception as e:
            print(f"[小数] 创建经验文档失败: {e}")

        # 2. 生成数据分析文档
        analysis_doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            ana_markdown = self._format_analysis_doc(topic_title, data_record, analysis)
            ana_doc_id = doc_storage.create_doc(f"[数据分析] {date_str} {topic_title}")
            doc_storage.append_section(ana_doc_id, ana_markdown)
            doc_storage.set_permissions(ana_doc_id, share_type="tenant_readable")
            analysis_doc_url = doc_storage.get_share_url(ana_doc_id)
            print(f"[小数] 创建数据分析文档: {topic_title[:30]}...")
        except Exception as e:
            print(f"[小数] 创建数据分析文档失败: {e}")

        # 3. 更新 DATA 表
        if data_id:
            try:
                self.storage.update("数据库", data_id, {
                    "经验文档链接": exp_doc_url,
                    "数据分析文档链接": analysis_doc_url,
                    "数据状态": "已分析",
                })
                print(f"[小数] DATA {data_id} 更新文档链接")
            except Exception as e:
                print(f"[小数] 更新 DATA 失败: {e}")

        result["exp_doc_url"] = exp_doc_url
        result["analysis_doc_url"] = analysis_doc_url

    def _format_experience_doc(self, topic_title: str, analysis: dict) -> str:
        """格式化经验总结文档"""
        experiences = analysis.get("可沉淀经验", [])
        suggestions = analysis.get("选题策略优化建议", [])

        md = f"# [经验] {topic_title}\n\n"
        md += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        md += "---\n\n"

        md += "## 可沉淀经验\n\n"
        for i, exp in enumerate(experiences, 1):
            md += f"{i}. {exp}\n\n"

        md += "## 选题策略优化建议\n\n"
        for i, sug in enumerate(suggestions, 1):
            md += f"{i}. {sug}\n\n"

        md += "## 平台表现总结\n\n"
        platform = analysis.get("平台表现", {})
        md += f"- 最佳平台: {platform.get('最佳平台', 'N/A')}\n"
        md += f"- 最差平台: {platform.get('最差平台', 'N/A')}\n"
        md += f"- 分析: {platform.get('分析', 'N/A')}\n\n"

        return md

    def _format_analysis_doc(self, topic_title: str, data: dict, analysis: dict) -> str:
        """格式化数据分析文档"""
        md = f"# [数据分析] {topic_title}\n\n"
        md += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        md += "---\n\n"

        md += "## 综合评分\n\n"
        md += f"- 综合评分: {data.get('综合评分', 'N/A')}\n"
        md += f"- 爆点验证: {data.get('爆点验证', 'N/A')}\n\n"

        md += "## 各平台数据\n\n"
        md += f"| 平台 | 阅读量/播放量 | 点赞 | 其他 |\n"
        md += f"|------|--------------|------|------|\n"
        md += f"| 公众号 | {data.get('公众号_阅读量', 0)} | {data.get('公众号_点赞数', 0)} | 在看 {data.get('公众号_在看数', 0)} |\n"
        md += f"| 小红书 | {data.get('小红书_阅读量', 0)} | {data.get('小红书_点赞数', 0)} | 收藏 {data.get('小红书_收藏数', 0)} 评论 {data.get('小红书_评论数', 0)} |\n"
        md += f"| 抖音 | {data.get('抖音_播放量', 0)} | {data.get('抖音_点赞数', 0)} | 评论 {data.get('抖音_评论数', 0)} |\n"
        md += f"| 视频号 | {data.get('视频号_播放量', 0)} | {data.get('视频号_点赞数', 0)} | 转发 {data.get('视频号_转发数', 0)} |\n"
        md += f"| B站 | {data.get('B站_播放量', 0)} | {data.get('B站_点赞数', 0)} | 投币 {data.get('B站_投币数', 0)} |\n\n"

        md += "## 数据与内容关联分析\n\n"
        md += analysis.get("数据与内容关联分析", "（无分析内容）") + "\n\n"

        return md


Analyst = AnalystAgent
