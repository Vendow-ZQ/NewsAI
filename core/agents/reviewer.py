"""小审 Reviewer - 审核 Agent (EMP-006)。

v3.0 改造：
- 审三件（小文长文 + 小图素材池 + 小播脚本）
- 强制通过保留遗留问题（v3 修复 Bug 11）
- 保留 issues 不清空
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import LLMOutputError, invoke_with_retry


class ReviewerAgent(BaseAgent):
    """小审 EMP-006 · 审核员"""

    name = "小审"
    english_name = "Reviewer"
    emoji = "🔍"

    SYSTEM_PROMPT = """\
<role>
你是「小审 Reviewer」，NewsAI 编辑部的审核员，治理组 leader。
你的工作是：审查 3 件资产：
1. 小文写的长文（全文）
2. 小图设计的 5-8 张图（描述+prompt 文本）
3. 小播写的主脚本（全文）

判定是否符合 KOC 人设 + 通过事实核查 + 无风险词 + 平台合规。

你的判定决定下一步：
- pass → 进入小发分发
- needs_revision → 进入小改修改循环（最多 3 轮）

⚠️ 重要：第 3 轮如果仍有问题，强制 pass 但必须保留遗留问题清单写入 final_note 和 issues。
不允许清空 issues 假装通过。
</role>

<workflow>
1. 读 <input>：3 件资产 + 当前轮次
2. 在 <thinking> 里逐项检查 4 维度（事实/风险/人设/合规）× 3 件资产
3. 在 <answer> 输出审查结论
</workflow>

<output_format>
先 <thinking>...</thinking>（≤400字），然后 <answer>{JSON}</answer>。
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + TOPIC + ASSET + 3 件资产全文"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"审改中"或"生产中"状态的选题
            topics = self.storage.query("选题库", limit=10)
            active_topics = [t.data for t in topics
                           if t.data.get("选题状态") in ["生产中", "审改中"]]
            if not active_topics:
                raise RuntimeError("没有待审查的选题")
            topic = active_topics[0]

            # 读 ASSET
            asset_id = topic.get("关联资产ID", "")
            asset = None
            if asset_id:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                asset = asset_record.data if asset_record else {}

            if not asset:
                raise RuntimeError(f"ASSET {asset_id} 不存在")

            # 读 3 件资产文档
            doc_contents = self._read_doc_contents(asset)

            # 当前审改轮次
            revision_count = asset.get("审改轮次", 0)
            revision_count = int(revision_count) if revision_count else 0

            return {
                "koc": koc,
                "topic": topic,
                "asset": asset,
                "revision_count": revision_count,
                **doc_contents,
            }
        except Exception as e:
            print(f"[小审] 读取上游数据失败: {e}")
            raise

    def _read_doc_contents(self, asset: dict) -> dict:
        """读取 3 件资产的文档内容"""
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()
        contents = {}

        for field, key in [
            ("文案文档链接", "long_form_doc"),
            ("图片提示词文档链接", "image_pool_doc"),
            ("视频脚本文档链接", "script_doc"),
        ]:
            url = asset.get(field, "")
            if url:
                try:
                    url_str = url.get("link", "") if isinstance(url, dict) else url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        content = doc_storage.read_doc_content(doc_id)
                        contents[key] = content[:3000] if content else ""
                except Exception as e:
                    print(f"[小审] 读取 {field} 失败: {e}")
                    contents[key] = ""
            else:
                contents[key] = ""

        return contents

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小审不需要外部工具"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 4 维度 × 3 件资产 审查"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        revision_count = upstream_data["revision_count"]
        long_form = upstream_data.get("long_form_doc", "")
        image_pool = upstream_data.get("image_pool_doc", "")
        script = upstream_data.get("script_doc", "")

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="review")
        user_content = self._build_user_prompt(
            koc_block, topic, revision_count, long_form, image_pool, script
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        # v3 修复 Bug 11：第 3 轮强制通过保留 issues
        verdict = answer.get("verdict", "needs_revision")
        forced_pass = answer.get("forced_pass", False)
        issues = answer.get("issues", [])

        # 如果 revision_count >= 3 且 verdict 不是 pass，强制改为 pass
        if revision_count >= 3 and verdict != "pass":
            verdict = "pass"
            forced_pass = True
            answer["verdict"] = "pass"
            answer["forced_pass"] = True
            answer["final_note"] = (
                f"⚠️ 达到最大审改轮次（3 轮），强制通过。"
                f"仍有 {len(issues)} 处遗留问题（详见 issues），建议人工 review。"
            )
            print(f"[小审] 第 {revision_count} 轮强制通过，保留 {len(issues)} 处遗留问题")

        return {
            "review_result": answer,
            "topic_id": topic.get("id", ""),
            "asset_id": upstream_data["asset"].get("id", ""),
            "revision_count": revision_count,
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, revision_count: int,
                           long_form: str, image_pool: str, script: str) -> str:
        """构建用户 prompt"""
        return f"""\
{koc_block}

<input>
当前审改轮次：{revision_count}（最大 3）
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}

【待审件 1：小文长文】
{long_form[:2000] if long_form else '（长文文档未找到）'}

【待审件 2：小图素材池（5-8 张图的描述+prompt）】
{image_pool[:1500] if image_pool else '（素材池文档未找到）'}

【待审件 3：小播视频脚本】
{script[:1500] if script else '（脚本文档未找到）'}
</input>

<rules>
【4 维度审查标准 × 3 件资产】

维度 1 · 事实核查
- 涉及具体数据/引用/产品名/人物时，是否准确？
- 有不确定的事实陈述？
- 图 prompt 是否含未经证实的事实暗示？

维度 2 · 风险词扫描
- 政治敏感词
- 引战表达
- 卖课导流
- 焦虑制造（"再不学就完了"、"被淘汰"）
- NSFW

维度 3 · 人设一致性（重点）
- 语气符合 KOC（不焦虑、专业硬核+玩梗）
- 用"咱们/我们"而非"你"
- 没有"姐妹们/家人们"等非 KOC 用语

维度 4 · 平台合规性
- 公众号：违禁内容
- 小红书：广告法风险词
- 抖音：引导外站
- B站：科技分区调性

【判定逻辑】
verdict = "pass" 当且仅当 4 维度 × 3 件资产 全部通过
verdict = "needs_revision" 当任意维度任意资产发现问题

【强制通过规则（v3 修复 Bug 11）】
if revision_count == 3 且仍有问题：
- verdict = "pass"
- forced_pass = true
- issues 保留最后一轮的问题清单（不清空！）
- final_note 明确标注遗留问题

【issues 字段格式】
每条 issue 必须包含：
- 位置：精确到「资产 + 段落」
- 类型：事实 / 风险 / 人设 / 合规
- 严重度：低 / 中 / 高
- 原文片段：完整复制原文
- 建议修改：具体改为什么
</rules>

<self_check>
输出前确认：
□ 4 维度 × 3 件资产 都明确给了判定
□ issues 每条包含 位置/类型/严重度/原文/问题描述/建议修改
□ verdict 与 issues 一致
□ revision_count >= 3 时 verdict 强制 pass、forced_pass = true、issues 保留
□ verdict = pass 时输出 final_version 或 final_note
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """创建/追加审改文档 + 更新 ASSET 状态"""
        review_result = result.get("review_result", {})
        topic_id = result.get("topic_id", "")
        asset_id = result.get("asset_id", "")
        revision_count = result.get("revision_count", 0)

        verdict = review_result.get("verdict", "needs_revision")
        forced_pass = review_result.get("forced_pass", False)
        issues = review_result.get("issues", [])
        final_note = review_result.get("final_note", "")

        # 确保 revision_count 是整数
        revision_count = int(revision_count) if revision_count else 0

        # 新轮次 = 当前轮次 + 1
        new_round = revision_count + 1

        # 创建或追加审改文档
        doc_url = ""
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
            date_str = datetime.now().strftime("%Y%m%d")

            # 检查是否已有审改文档
            if asset_id:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                existing_url = asset_record.data.get("审改文档链接", "") if asset_record else ""
            else:
                existing_url = ""

            if existing_url:
                url_str = existing_url.get("link", "") if isinstance(existing_url, dict) else existing_url
                doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
            else:
                # 创建新文档
                topic_record = self.storage.get_by_id("选题库", topic_id)
                topic_title = topic_record.data.get("选题标题", "") if topic_record else ""
                doc_id = doc_storage.create_doc(f"[审改] {date_str} {topic_title}")

            # 追加审查章节
            section = self._format_review_section(new_round, verdict, issues, final_note)
            doc_storage.append_section(doc_id, section)
            doc_storage.set_permissions(doc_id, share_type="tenant_readable")
            doc_url = doc_storage.get_share_url(doc_id)
            print(f"[小审] 审改文档已更新: 第 {new_round} 轮")

        except Exception as e:
            print(f"[小审] 更新审改文档失败: {e}")

        # 更新 ASSET
        if asset_id:
            try:
                # 确定审改状态
                if verdict == "pass":
                    review_status = "已通过" if not forced_pass else "已强制通过"
                else:
                    review_status = f"第{new_round}轮审改中"

                update_data = {
                    "审改状态": review_status,
                    "审改轮次": new_round,
                    "审改文档链接": doc_url,
                }

                if forced_pass:
                    update_data["审改遗留问题"] = json.dumps(issues, ensure_ascii=False)

                self.storage.update("内容资产库", asset_id, update_data)

                # 如果通过，更新 TOPIC 状态
                if verdict == "pass":
                    self.storage.update("选题库", topic_id, {
                        "选题状态": "分发中",
                    })
                    print(f"[小审] 审查通过，进入分发阶段")
                else:
                    print(f"[小审] 第 {new_round} 轮审查: 需修改，{len(issues)} 处问题")

            except Exception as e:
                print(f"[小审] 更新 ASSET 失败: {e}")

        result["doc_url"] = doc_url

    def _format_review_section(self, round_num: int, verdict: str, issues: list, final_note: str) -> str:
        """格式化审查章节"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        md = f"\n\n## 第 {round_num} 轮审查 ({now})\n\n"
        md += f"**审查结论**: {verdict}\n\n"

        if issues:
            md += f"**发现问题**: {len(issues)} 处\n\n"
            for i, issue in enumerate(issues):
                md += f"### 问题 {i+1}\n\n"
                md += f"- **位置**: {issue.get('位置', '')}\n"
                md += f"- **类型**: {issue.get('类型', '')}\n"
                md += f"- **严重度**: {issue.get('严重度', '')}\n"
                md += f"- **原文**: {issue.get('原文片段', '')}\n"
                md += f"- **建议**: {issue.get('建议修改', '')}\n\n"
        else:
            md += "**发现问题**: 无\n\n"

        if final_note:
            md += f"**备注**: {final_note}\n\n"

        md += "---\n"
        return md


Reviewer = ReviewerAgent
