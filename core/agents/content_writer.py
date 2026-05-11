"""小文 ContentWriter - 文字编辑 Agent (EMP-003)。

v3.0 改造：
- 写 1 篇长文不分平台（v2 写 4 平台版本）
- 这是给小发后续做 4 平台分发改写的"源稿"
- 至少 5 个 [配图N: 描述] 占位
- 修复 KOC 注入
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.chinese_hooks import CHINESE_HOOKS_BLOCK
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class ContentWriterAgent(BaseAgent):
    """小文 EMP-003 · 文字编辑"""

    name = "小文"
    english_name = "ContentWriter"
    emoji = "✍️"

    SYSTEM_PROMPT = """\
<role>
你是「小文 ContentWriter」，NewsAI 编辑部的文字编辑，生产组成员。
你的工作是：根据选定的选题，写一篇 1000-3000 字的高质量长文。
你不分平台——这是给小发后续做 4 平台分发改写的"源稿"。
你写完后不再修改——审改循环由小审 + 小改负责。
</role>

<workflow>
1. 读 <input>：选题方案 + 关联热帖原文（事实核查用）
2. 在 <thinking> 里规划：
   - 长文结构（开头钩子 → 主体 → 结尾互动）
   - 信息密度规划（每 100 字 1 个 takeaway）
   - 配图占位位置（用 [配图N: 描述] 标记）
3. 在 <answer> 输出长文完整内容
</workflow>

<output_format>
先在 <thinking>...</thinking> 写规划（≤200字），
然后 <answer>{长文 JSON}</answer>。
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + TOPIC（已选中）+ TREND（事实核查）"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"已选中"状态的选题
            topics = self.storage.query("选题库", limit=10)
            selected_topics = [t.data for t in topics if t.data.get("选题状态") == "已选中"]

            if not selected_topics:
                raise RuntimeError("没有'已选中'状态的选题")

            topic = selected_topics[0]

            # 读关联热帖（事实核查用）
            trend_ids = []
            try:
                trend_ids_raw = topic.get("关联热帖IDs", "[]")
                if isinstance(trend_ids_raw, str):
                    trend_ids = json.loads(trend_ids_raw)
                else:
                    trend_ids = trend_ids_raw
            except Exception:
                trend_ids = []

            trends = []
            for tid in trend_ids:
                try:
                    trend = self.storage.get_by_id("热帖库", tid)
                    if trend:
                        trends.append(trend.data)
                except Exception:
                    pass

            return {"koc": koc, "topic": topic, "trends": trends}
        except Exception as e:
            print(f"[小文] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """切换 ASSET 状态：未开始 → 生产中"""
        topic = upstream_data["topic"]
        asset_id = topic.get("关联资产ID", "")

        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "文案状态": "生产中",
                    "生产开始时间": current_timestamp_ms(),
                })
                # 同步 TOPIC.选题状态: 已选中 → 生产中
                self.storage.update("选题库", topic["id"], {
                    "选题状态": "生产中",
                })
                print(f"[小文] ASSET {asset_id} 文案状态: 生产中")
            except Exception as e:
                print(f"[小文] 更新 ASSET 状态失败: {e}")

        return {"asset_id": asset_id}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 写 1 篇长文"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        trends = upstream_data["trends"]

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="creation")
        user_content = self._build_user_prompt(koc_block, topic, trends)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        return {
            "long_form_content": answer,
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "asset_id": tool_results.get("asset_id", ""),
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, trends: list) -> str:
        """构建用户 prompt"""
        # 关联热帖信息
        trends_text = ""
        for t in trends:
            trends_text += f"""\
- 平台：{t.get('信源平台', '')}
- 标题：{t.get('标题', '')}
- 摘要：{t.get('原文摘要', '')[:300]}
- 链接：{t.get('原文链接', '')}

"""

        return f"""\
{koc_block}

{CHINESE_HOOKS_BLOCK}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}
预估受众：{topic.get('预估受众', '')}
钩子类型：{topic.get('钩子类型', '')}

关联热帖原文（用于事实核查）：
{trends_text}
</input>

<rules>
【长文写作铁律】

1. 字数：1000-3000 字（不强求 1500+）

2. 结构（必须遵循）：
   - 开头：3-5 句钩子，引发往下读
   - 主体：3-5 段，每段一个独立小结论
   - 结尾：必有评论引导

3. 标题：
   - 与选题标题相同或微调
   - 前 8 字必有钩子

4. 配图占位（关键！）：
   - 用 [配图1: 描述] 标记
   - 至少 5 个配图占位（给小图用 5-8 张图素材池做参考）
   - 每个占位都说清楚要传达什么

5. 信息密度：每 100 字至少 1 个具体细节
   - 数据 / 引用 / 工具名 / 操作步骤
   - 没具体 = 水文

6. 风格红线（KOC 准则）：
   - 用"咱们/我们"，不用"你"
   - 不写焦虑话术
   - 不卖课不导流
   - 不站队任何厂商

7. 不分平台：
   - 不要写"公众号版""小红书版"
   - 这是"源稿"，小发会拆 4 平台
</rules>

<self_check>
输出前确认：
□ 字数 1000-3000 字
□ 标题前 8 字真有钩子
□ 全程用"咱们/我们"，不用"你"
□ 没有焦虑话术 / 卖课 / 站队
□ 至少 5 个 [配图N: 描述] 占位
□ 每个配图占位都说清要传达什么
□ 结尾有评论引导
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """创建飞书云文档 + 更新 ASSET 状态"""
        topic_id = result.get("topic_id", "")
        topic_title = result.get("topic_title", "")
        asset_id = result.get("asset_id", "")
        content = result.get("long_form_content", {})

        # 格式化长文为 Markdown
        markdown = self._format_long_form(content)

        # 创建飞书云文档
        doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            date_str = datetime.now().strftime("%Y%m%d")
            doc_id = doc_storage.create_post_doc(topic_title, date_str)
            doc_storage.append_section(doc_id, markdown)
            doc_storage.set_permissions(doc_id, share_type="tenant_readable")
            doc_url = doc_storage.get_share_url(doc_id)
            print(f"[小文] 创建文案文档: {topic_title[:30]}...")
        except Exception as e:
            print(f"[小文] 创建文案文档失败: {e}")

        # 更新 ASSET
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "文案状态": "已完成",
                    "文案文档链接": doc_url,
                })
                print(f"[小文] ASSET {asset_id} 文案状态: 已完成")
            except Exception as e:
                print(f"[小文] 更新 ASSET 失败: {e}")

        result["doc_url"] = doc_url

    def _format_long_form(self, content: dict) -> str:
        """格式化长文为 Markdown"""
        title = content.get("标题", "")
        body = content.get("正文", "")
        word_count = content.get("字数", 0)
        placeholders = content.get("配图占位", [])

        md = f"# {title}\n\n"
        md += f"*{word_count} 字*\n\n"
        md += "---\n\n"
        md += body
        md += "\n\n---\n\n"
        md += "## 配图占位清单\n\n"
        for ph in placeholders:
            md += f"- {ph}\n"

        return md


ContentWriter = ContentWriterAgent
