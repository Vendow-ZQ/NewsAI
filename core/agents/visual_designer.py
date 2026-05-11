"""小图 VisualDesigner - 视觉设计 Agent (EMP-004)。

v3.0 改造：
- 产出 5-8 张图素材池（不再是配图方案 JSON）
- 读小文长文全文（v3 修复 Bug 7）
- 每张图标注适用平台
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class VisualDesignerAgent(BaseAgent):
    """小图 EMP-004 · 视觉设计师"""

    name = "小图"
    english_name = "VisualDesigner"
    emoji = "🎨"

    SYSTEM_PROMPT = """\
<role>
你是「小图 VisualDesigner」，NewsAI 编辑部的视觉设计师，生产组成员。
你的工作是为这次选题产出 5-8 张图的描述 + prompt，作为「素材池」给小发分发时挑选。
你不直接产出图片本身——你产出的是「图的设计方案」。

3 类图你都要会做：
1. 文字卡片图（HTML 模板渲染，最常用）
2. 信息图（SVG 模板，对比/流程/数据类）
3. AI 画面图（即梦 API，需要画面感时用）
</role>

<workflow>
1. 读 <input>：选题 + 小文写的长文（含配图占位）
2. 在 <thinking> 里：
   - 长文里的 5+ 配图占位每个适合哪种类型？
   - 还需要补充哪些图作为"素材池"（封面/总结金句/分享卡片等）？
3. 在 <answer> 输出 5-8 张图的完整设计
</workflow>

<output_format>
先 <thinking>...</thinking>（≤200字），然后 <answer>{JSON}</answer>。
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

            # 读小文的长文（如果有）
            long_form_content = ""
            if asset and asset.get("文案文档链接"):
                try:
                    from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                    doc_storage = FeishuDocStorage()
                    doc_url = asset["文案文档链接"]
                    url_str = doc_url.get("link", "") if isinstance(doc_url, dict) else doc_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        long_form_content = doc_storage.read_doc_content(doc_id) or ""
                except Exception as e:
                    print(f"[小图] 读取长文失败: {e}")

            return {
                "koc": koc,
                "topic": topic,
                "asset": asset or {},
                "long_form_content": long_form_content,
            }
        except Exception as e:
            print(f"[小图] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """切换 ASSET 状态：未开始 → 生产中"""
        asset = upstream_data.get("asset", {})
        asset_id = asset.get("id", "")
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "配图状态": "生产中",
                })
                print(f"[小图] ASSET {asset_id} 配图状态: 生产中")
            except Exception as e:
                print(f"[小图] 更新 ASSET 状态失败: {e}")
        return {"asset_id": asset_id}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 设计 5-8 张图"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        long_form = upstream_data.get("long_form_content", "")

        # 提取配图占位
        placeholders = _extract_image_placeholders(long_form)

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="visual")
        user_content = self._build_user_prompt(koc_block, topic, long_form, placeholders)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        return {
            "image_pool": answer.get("图素材池", []),
            "strategy": answer.get("素材池策略", ""),
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "asset_id": tool_results.get("asset_id", ""),
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, long_form: str, placeholders: list) -> str:
        """构建用户 prompt"""
        placeholders_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(placeholders)) if placeholders else "（小文未标记配图占位）"

        return f"""\
{koc_block}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
钩子类型：{topic.get('钩子类型', '')}

小文写的长文（用于理解配图位置）：
{long_form[:2000] if long_form else '（长文尚未生成或读取失败）'}

长文中的配图占位（小文标记的，至少 5 个）：
{placeholders_text}
</input>

<rules>
【3 类图选择决策树】

→ 对比/数据/流程类（开/关对比、3 步教程、数据图） → 信息图（SVG）
→ 封面/金句/重点类（标题卡片、摘要金句） → 文字卡片图（HTML）
→ 画面感/抽象意象类（"未来感办公场景"） → AI 画面图（即梦 prompt）

【输出 5-8 张图素材池的结构】

必须覆盖以下用途（小发后续会按平台选用）：
1. 「封面金句卡」（必须）—— 通用封面，文字卡片图
2. 「正文配图 1-N」（对应小文的配图占位）—— 各类型混搭
3. 「总结对照图」（必须）—— 信息图（对比/清单类）
4. 「金句卡片 1-2 张」—— 文字卡片图（适合小红书）

【每张图的输出字段（不同类型不同）】

通用字段：
- 图编号（"图1", "图2"...）
- 用途（封面 / 正文配图 / 总结 / 金句）
- 图类型（文字卡片 / 信息图 / AI画面图）
- 描述（一句话说明传达什么）
- 适用平台（小发分发时参考）

文字卡片图额外：
- template（card_white / card_dark / card_emoji / card_minimal）
- main_text（主文字，≤15字）
- sub_text（副文字，≤25字，可空）
- accent_emoji（点缀 emoji）

信息图额外：
- template（infographic_compare / infographic_steps / infographic_data / infographic_checklist）
- title（图标题）
- data（结构化数据，与 template 匹配）

AI 画面图额外：
- jimeng_prompt（即梦 prompt，中文，描述画面）
- aspect_ratio（1:1 / 16:9 / 9:16）
- negative_prompt（避免出现的元素）
- 风格描述（如"极简 UI / 商务摄影 / 二次元卡通"）

【图片素材池规划原则】
- 总数 5-8 张（不要超）
- 至少 3 张文字卡片（最常用）
- 1-2 张信息图（强力传播工具）
- 0-2 张 AI 画面图（增强视觉冲击）
- 平台适配：覆盖小红书（图文 9 张需求）+ 公众号（3-5 张）+ B站（封面）
</rules>

<self_check>
输出前确认：
□ 图素材池数量 5-8 张
□ 每张图都标注 "图编号" 和 "适用平台"
□ 文字卡片 main_text ≤ 15 字
□ 信息图 data 字段结构匹配 template
□ AI 画面图 prompt 含场景 + 风格 + 否定词
□ 至少 1 张"封面"用途、1 张"总结"用途
□ 总数不超 8 张
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """创建图片提示词文档 + 更新 ASSET 状态"""
        topic_id = result.get("topic_id", "")
        topic_title = result.get("topic_title", "")
        asset_id = result.get("asset_id", "")
        image_pool = result.get("image_pool", [])

        # 格式化素材池为 Markdown
        markdown = self._format_image_pool(image_pool, topic_title)

        # 创建飞书云文档
        doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            date_str = datetime.now().strftime("%Y%m%d")
            doc_id = doc_storage.create_doc(f"[配图] {date_str} {topic_title}")
            doc_storage.append_section(doc_id, markdown)
            doc_storage.set_permissions(doc_id, share_type="tenant_readable")
            doc_url = doc_storage.get_share_url(doc_id)
            print(f"[小图] 创建配图文档: {topic_title[:30]}...")
        except Exception as e:
            print(f"[小图] 创建配图文档失败: {e}")

        # 更新 ASSET
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "配图状态": "已完成",
                    "图片提示词文档链接": doc_url,
                })
                print(f"[小图] ASSET {asset_id} 配图状态: 已完成")
            except Exception as e:
                print(f"[小图] 更新 ASSET 失败: {e}")

        result["doc_url"] = doc_url

    def _format_image_pool(self, image_pool: list, topic_title: str) -> str:
        """格式化图素材池为 Markdown"""
        md = f"# [配图] {topic_title}\n\n"
        md += f"*共 {len(image_pool)} 张图*\n\n---\n\n"

        for img in image_pool:
            md += f"## {img.get('图编号', '')} · {img.get('用途', '')}\n\n"
            md += f"**类型**: {img.get('图类型', '')}\n\n"
            md += f"**描述**: {img.get('描述', '')}\n\n"
            md += f"**适用平台**: {', '.join(img.get('适用平台', []))}\n\n"

            img_type = img.get("图类型", "")
            if img_type == "文字卡片":
                md += f"- template: `{img.get('template', '')}`\n"
                md += f"- main_text: `{img.get('main_text', '')}`\n"
                md += f"- sub_text: `{img.get('sub_text', '')}`\n"
                md += f"- accent_emoji: {img.get('accent_emoji', '')}\n"
            elif img_type == "信息图":
                md += f"- template: `{img.get('template', '')}`\n"
                md += f"- title: `{img.get('title', '')}`\n"
                md += f"- data: `{json.dumps(img.get('data', {}), ensure_ascii=False)}`\n"
            elif img_type == "AI画面图":
                md += f"- jimeng_prompt: `{img.get('jimeng_prompt', '')}`\n"
                md += f"- aspect_ratio: `{img.get('aspect_ratio', '')}`\n"
                md += f"- negative_prompt: `{img.get('negative_prompt', '')}`\n"
                md += f"- 风格: `{img.get('风格描述', '')}`\n"

            md += "\n---\n\n"

        return md


# =============================================================================
# 辅助函数
# =============================================================================

def _extract_image_placeholders(content: str) -> list:
    """从长文中提取 [配图N: 描述] 占位"""
    import re
    if not content:
        return []
    pattern = r'\[配图\d+:\s*([^\]]+)\]'
    matches = re.findall(pattern, content)
    return matches


VisualDesigner = VisualDesignerAgent
