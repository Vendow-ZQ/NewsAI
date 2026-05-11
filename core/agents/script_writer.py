"""小播 ScriptWriter - 短视频编剧 Agent (EMP-005)。

v3.0 改造：
- 读小文长文全文（v3 修复 Bug 7：不限字数）
- 出 1 个 1-3 分钟主脚本（不再分 4 平台）
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class ScriptWriterAgent(BaseAgent):
    """小播 EMP-005 · 短视频编剧"""

    name = "小播"
    english_name = "ScriptWriter"
    emoji = "🎬"

    SYSTEM_PROMPT = """\
<role>
你是「小播 ScriptWriter」，NewsAI 编辑部的短视频编剧，生产组成员。
你的工作是：根据选题 + 小文的长文，写一份 1-3 分钟的主视频脚本。
注意：你只出 1 个主脚本——小发分发时会标注"抖音版剪辑指引"（保留哪些镜头）。
你的脚本必须包含：完整台本 / 分镜 / 时长 / 钩子开场 / 核心内容 / CTA / 字幕 / BGM建议 / 镜头清单。
</role>

<workflow>
1. 读 <input>：选题 + 小文的长文（全文）
2. 在 <thinking> 里规划：
   - 主脚本总时长（1-3 分钟）
   - 钩子开场（≤3 秒）的具体设计
   - 主体节奏（每 5-10 秒一个镜头切换）
   - CTA 设计
3. 在 <answer> 输出完整脚本
</workflow>

<output_format>
先 <thinking>...</thinking>（≤200字），然后 <answer>{JSON}</answer>。

【脚本 JSON 结构】
{
  "总时长": "1-3分钟",
  "钩子类型": "反差/数字/提问/身份代入",
  "钩子开头": {"时间": "00:00-00:05", "画面": "", "口播": "", "字幕": ""},
  "核心内容": [{"段落": "", "时间": "", "画面": "", "口播": "", "字幕": ""}],
  "CTA": {"时间": "", "画面": "", "口播": "", "字幕": ""},
  "镜头清单": [
    {"时间码": "00:00:00~00:00:15", "画面": "", "口播": "", "字幕": ""}
  ],
  "BGM建议": "",
  "剪辑节奏说明": ""
}

镜头清单时间码格式统一用 00:00:00~00:00:15 这种格式，简洁明了
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + TOPIC + ASSET + 小文长文全文"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"生产中"状态的选题
            topics = self.storage.query("选题库", limit=10)
            active_topics = [t.data for t in topics if t.data.get("选题状态") in ["已选中", "生产中"]]
            if not active_topics:
                raise RuntimeError("没有活跃选题")
            topic = active_topics[0]

            # 读 ASSET
            asset_id = topic.get("关联资产ID", "")
            asset = None
            if asset_id:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                asset = asset_record.data if asset_record else {}

            # 读小文的长文全文（v3 修复 Bug 7：不限字数）
            long_form_full = ""
            if asset and asset.get("文案文档链接"):
                try:
                    from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                    doc_storage = FeishuDocStorage()
                    doc_url = asset["文案文档链接"]
                    url_str = doc_url.get("link", "") if isinstance(doc_url, dict) else doc_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        long_form_full = doc_storage.read_doc_content(doc_id) or ""
                except Exception as e:
                    print(f"[小播] 读取长文失败: {e}")

            return {
                "koc": koc,
                "topic": topic,
                "asset": asset or {},
                "long_form_full": long_form_full,
            }
        except Exception as e:
            print(f"[小播] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """切换 ASSET 状态：未开始 → 生产中"""
        asset = upstream_data.get("asset", {})
        asset_id = asset.get("id", "")
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "视频状态": "生产中",
                })
                print(f"[小播] ASSET {asset_id} 视频状态: 生产中")
            except Exception as e:
                print(f"[小播] 更新 ASSET 状态失败: {e}")
        return {"asset_id": asset_id}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 写 1 个主脚本"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        long_form = upstream_data.get("long_form_full", "")

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="creation")
        user_content = self._build_user_prompt(koc_block, topic, long_form)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        return {
            "script": answer,
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "asset_id": tool_results.get("asset_id", ""),
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, long_form: str) -> str:
        """构建用户 prompt"""
        # v3 修复 Bug 7：不再截断为 1500 字，读全文
        long_form_text = long_form if long_form else "（长文尚未生成）"

        return f"""\
{koc_block}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}
钩子类型：{topic.get('钩子类型', '')}

小文写的长文全文（v3 修复 Bug 7：不再截断为 1500 字）：
{long_form_text}
</input>

<rules>
【主脚本铁律（1-3 分钟）】

1. 时长：1-3 分钟（默认 1 分 30 秒-2 分钟）
2. 结构：
   - 钩子开场（0-5 秒）
   - 核心内容（5 秒-总时长-10秒，分 2-4 个小段）
   - CTA（最后 5-10 秒）

3. 钩子开场（关键！）：
   - ≤ 3 秒抓住人
   - 反差 / 数字 / 提问 / 身份代入 4 选 1
   - 与选题钩子类型一致

4. 镜头清单（核心交付）：
   每行包含：
   - 时间段（如 "0-3s"）
   - 画面：具体描述（不要"主持人讲话"这种空话）
   - 口播：当前时段的口播文案
   - 字幕：精简版的关键词（比口播短 30%）

5. CTA：
   - "关注/点赞/收藏" 选 1-2 个，不要全要
   - 与 KOC 调性一致（"咱们一起学 AI 不焦虑"）

6. BGM 建议：
   - 风格描述（如"轻快电子节奏"、"Lofi 学习风"）

7. 不要直接写"4 平台脚本"！
   - 你只出 1 个主脚本
   - 小发会基于这份做抖音/小红书/B站/视频号的剪辑指引
</rules>

<self_check>
输出前确认：
□ 总时长 1-3 分钟
□ 钩子开场 ≤ 3 秒
□ 镜头清单每项都有 时间/画面/口播/字幕 4 个字段
□ 画面描述具体（不是"主持人讲话"这种空话）
□ 字幕比口播精简 30%+
□ CTA 不滥用（关注/点赞/收藏选 1-2 个）
□ BGM 建议有具体风格描述
□ 没有写"抖音版/B站版"——只有 1 个主脚本
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """创建视频脚本文档 + 更新 ASSET 状态"""
        topic_id = result.get("topic_id", "")
        topic_title = result.get("topic_title", "")
        asset_id = result.get("asset_id", "")
        script = result.get("script", {})

        # 格式化脚本为 Markdown
        markdown = self._format_script(script, topic_title)

        # 创建飞书云文档
        doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            date_str = datetime.now().strftime("%Y%m%d")
            doc_id = doc_storage.create_doc(f"[脚本] {date_str} {topic_title}")
            doc_storage.append_section(doc_id, markdown)
            doc_storage.set_permissions(doc_id, share_type="tenant_readable")
            doc_url = doc_storage.get_share_url(doc_id)
            print(f"[小播] 创建脚本文档: {topic_title[:30]}...")
        except Exception as e:
            print(f"[小播] 创建脚本文档失败: {e}")

        # 更新 ASSET
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "视频状态": "已完成",
                    "视频脚本文档链接": doc_url,
                })
                print(f"[小播] ASSET {asset_id} 视频状态: 已完成")
            except Exception as e:
                print(f"[小播] 更新 ASSET 失败: {e}")

        result["doc_url"] = doc_url

    def _format_script(self, script: dict, topic_title: str) -> str:
        """格式化脚本为 Markdown"""
        md = f"# [脚本] {topic_title}\n\n"
        md += f"**总时长**: {script.get('总时长', '')}\n\n"
        md += f"**钩子类型**: {script.get('钩子类型', '')}\n\n"
        md += "---\n\n"

        # 钩子开场
        hook = script.get("钩子开场", {})
        if hook:
            md += "## 钩子开场\n\n"
            md += f"- 时间: {hook.get('时间', '')}\n"
            md += f"- 画面: {hook.get('画面', '')}\n"
            md += f"- 口播: {hook.get('口播', '')}\n"
            md += f"- 字幕: {hook.get('字幕', '')}\n\n"

        # 核心内容
        core = script.get("核心内容", [])
        if core:
            md += "## 核心内容\n\n"
            for segment in core:
                md += f"### {segment.get('段落', '')} ({segment.get('时间', '')})\n\n"
                md += f"- 画面: {segment.get('画面', '')}\n"
                md += f"- 口播: {segment.get('口播', '')}\n"
                md += f"- 字幕: {segment.get('字幕', '')}\n\n"

        # CTA
        cta = script.get("CTA", {})
        if cta:
            md += "## CTA\n\n"
            md += f"- 时间: {cta.get('时间', '')}\n"
            md += f"- 画面: {cta.get('画面', '')}\n"
            md += f"- 口播: {cta.get('口播', '')}\n"
            md += f"- 字幕: {cta.get('字幕', '')}\n\n"

        # 镜头清单（时间码格式）
        shots = script.get("镜头清单", [])
        if shots:
            md += "## 镜头清单\n\n"
            for i, shot in enumerate(shots, 1):
                timecode = shot.get('时间码', shot.get('时间', f'镜头{i}'))
                scene = shot.get('画面', '')
                audio = shot.get('口播', '')
                subtitle = shot.get('字幕', '')
                md += f"**{timecode}** {scene}\n\n"
                if audio:
                    md += f"口播: {audio[:80]}{'...' if len(audio) > 80 else ''}\n\n"
                if subtitle:
                    md += f"字幕: *{subtitle}*\n\n"
                md += "---\n\n"

        # BGM
        bgm = script.get("BGM建议", "")
        if bgm:
            md += f"**BGM**: {bgm}\n\n"

        # 剪辑节奏
        rhythm = script.get("剪辑节奏说明", "")
        if rhythm:
            md += f"**剪辑节奏**: {rhythm}\n\n"

        return md


ScriptWriter = ScriptWriterAgent
