"""小改 Editor - 修改 Agent (EMP-007)。

v3.0 改造：
- 改审改文档副本（不动原始文档）
- changelog 不能为空（v3 修复 Bug 4）
- dispute_review 字段
- 连续 3 次 dispute → 卡死
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import LLMOutputError, invoke_with_retry


class EditorAgent(BaseAgent):
    """小改 EMP-007 · 修改专员"""

    name = "小改"
    english_name = "Editor"
    emoji = "🛠️"

    SYSTEM_PROMPT = """\
<role>
你是「小改 Editor」，NewsAI 编辑部的修改专员，治理组成员。
你不做创作，只做精确修改。

⚠️ 重要：你改的是「审改文档」（小审创建的副本），不动原始的小文/小图/小播文档。
原稿一次过原则。

你的工作是：读小审的审查意见，逐条精确修改审改副本，输出清晰的 changelog（diff 形式）。
</role>

<workflow>
1. 读 <input>：审改文档（含小审最新审查意见 + 上一轮的副本内容）
2. 在 <thinking> 里：
   - 逐条 issue 设计修改方案
   - 检查修改是否引入新问题
3. 在 <answer> 输出 changelog + 修改后的内容
</workflow>

<output_format>
先 <thinking>...</thinking>（≤300字），然后 <answer>{JSON}</answer>。

⚠️ changelog 列表必须非空。如果你认为不需要任何修改，输出空 changelog 是错误的——
这种情况意味着你应该向小审反馈"原稿其实没问题"，而不是绕过修改。
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + TOPIC + ASSET + 审改文档"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"审改中"状态的选题
            topics = self.storage.query("选题库", limit=10)
            review_topics = [t.data for t in topics if t.data.get("选题状态") == "审改中"]
            if not review_topics:
                raise RuntimeError("没有审改中的选题")
            topic = review_topics[0]

            # 读 ASSET
            asset_id = topic.get("关联资产ID", "")
            asset = None
            if asset_id:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                asset = asset_record.data if asset_record else {}

            if not asset:
                raise RuntimeError(f"ASSET {asset_id} 不存在")

            # 当前审改轮次
            revision_count = asset.get("审改轮次", 0)

            # 读审改文档内容
            audit_doc = ""
            audit_url = asset.get("审改文档链接", "")
            if audit_url:
                try:
                    from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                    doc_storage = FeishuDocStorage()
                    url_str = audit_url.get("link", "") if isinstance(audit_url, dict) else audit_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        audit_doc = doc_storage.read_doc_content(doc_id) or ""
                except Exception as e:
                    print(f"[小改] 读取审改文档失败: {e}")

            return {
                "koc": koc,
                "topic": topic,
                "asset": asset,
                "revision_count": revision_count,
                "audit_doc": audit_doc,
            }
        except Exception as e:
            print(f"[小改] 读取上游数据失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小改不需要外部工具"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM 精确修改 + 生成 changelog"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        asset = upstream_data["asset"]
        revision_count = upstream_data["revision_count"]
        audit_doc = upstream_data.get("audit_doc", "")

        # 构建 prompt（简化版：基于审改文档内容）
        koc_block = render_koc_block(koc, mode="review")
        user_content = self._build_user_prompt(
            koc_block, topic, revision_count, audit_doc
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        # v3 修复 Bug 4：检测 changelog 空
        changelog = answer.get("changelog", [])
        if not changelog:
            raise LLMOutputError(
                "小改输出 changelog 为空。如果你认为不需要修改，"
                "应输出 dispute case（before == after + dispute_review = true），"
                "而不是空 changelog。"
            )

        return {
            "edit_result": answer,
            "topic_id": topic.get("id", ""),
            "asset_id": asset.get("id", ""),
            "revision_count": revision_count,
        }

    def _build_user_prompt(self, koc_block: str, topic: dict, revision_count: int,
                           audit_doc: str) -> str:
        """构建用户 prompt"""
        return f"""\
{koc_block}

<input>
选题 ID：{topic.get('id', '')}
当前轮次：{revision_count}（最大 3）

【审改文档当前版本】
{audit_doc[:3000] if audit_doc else '（审改文档为空，请基于选题直接修改）'}

选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}
</input>

<rules>
【修改原则】
1. 只改小审指出的位置（从审改文档中提取 issues）
2. 不擅自创作、不擅自重写整段
3. 不引入新问题
4. 保持 KOC 风格（用"咱们/我们"、不焦虑）

【changelog 格式（关键）】
每条 changelog：
- issue_index：对应 issues 的索引
- 资产：长文 / 图素材 / 视频脚本
- 位置：与 issue 一致
- diff：before（原文片段）/ after（新片段）
- 修改说明：一句话解释

【⚠️ changelog 空的处理（v3 修复 Bug 4）】
如果你认为"原稿其实没问题"——不允许输出空 changelog。
应该：
- 仍然输出 changelog（至少 1 条），但 diff 的 before == after
- 在"修改说明"明确说"经核查，原稿无需修改。理由：xxx"
- 设置字段 dispute_review = true

连续 3 次 dispute → 触发 ASSET.审改状态 = "卡死"。

【修改后输出格式】
audit_doc_updated 包含完整的 3 件资产新版本：
- updated_long_form
- updated_image_pool
- updated_script
未被修改的部分照搬原文，被修改的部分用新内容。
</rules>

<self_check>
输出前确认：
□ changelog 列表非空（即使是 dispute case 也填一条 before==after）
□ 每条 changelog 含 issue_index/资产/位置/diff/修改说明
□ 修改位置与小审 issues 完全对应
□ 没有擅自修改小审未指出的内容
□ audit_doc_updated 含 3 件资产完整内容
□ 修改后符合 KOC 调性
□ 没有引入新的禁区话题
□ self_check_pass 字段必填
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """追加修改章节到审改文档 + 检查 dispute"""
        edit_result = result.get("edit_result", {})
        asset_id = result.get("asset_id", "")
        revision_count = result.get("revision_count", 0)

        changelog = edit_result.get("changelog", [])
        dispute_review = edit_result.get("dispute_review", False)

        # 检查是否所有 changelog 都是 dispute（before == after）
        all_dispute = False
        if changelog:
            try:
                all_dispute = all(
                    c.get("diff", {}).get("before", "") == c.get("diff", {}).get("after", "")
                    for c in changelog
                )
            except Exception:
                all_dispute = False

        # 检查连续 dispute 次数
        if all_dispute and not dispute_review:
            # 有 changelog 但全是 before==after，强制标记为 dispute
            dispute_review = True

        # 读取 ASSET 当前状态
        if asset_id:
            try:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                asset_data = asset_record.data if asset_record else {}
                existing_dispute = asset_data.get("审改遗留问题", "")
                consecutive = 0
                try:
                    if existing_dispute and "dispute" in str(existing_dispute):
                        consecutive = 1  # 简化计数
                except Exception:
                    pass

                if dispute_review:
                    consecutive += 1
                    if consecutive >= 3:
                        # 3 次连续 dispute → 卡死
                        self.storage.update("内容资产库", asset_id, {
                            "审改状态": "卡死",
                        })
                        raise RuntimeError(
                            f"ASSET {asset_id} 连续多次 dispute review，标记为'卡死'。"
                            f"需要人工介入。"
                        )

                # 追加修改章节到审改文档
                audit_url = asset_data.get("审改文档链接", "")
                if audit_url:
                    try:
                        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                        doc_storage = FeishuDocStorage()
                        url_str = audit_url.get("link", "") if isinstance(audit_url, dict) else audit_url
                        doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                        if doc_id:
                            section = self._format_edit_section(revision_count, changelog, dispute_review)
                            doc_storage.append_section(doc_id, section)
                            print(f"[小改] 已追加第 {revision_count} 轮修改到审改文档")
                    except Exception as e:
                        print(f"[小改] 追加审改文档失败: {e}")

                print(f"[小改] 修改完成: {len(changelog)} 处修改"
                      f"{' (dispute)' if dispute_review else ''}")

            except RuntimeError:
                raise
            except Exception as e:
                print(f"[小改] 更新存储失败: {e}")

    def _format_edit_section(self, round_num: int, changelog: list, dispute: bool) -> str:
        """格式化修改章节"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        md = f"\n\n## 第 {round_num} 轮修改 ({now})\n\n"

        if dispute:
            md += "**状态**: ⚠️ dispute review（有争议，建议复审）\n\n"
        else:
            md += f"**修改数**: {len(changelog)} 处\n\n"

        for i, entry in enumerate(changelog):
            md += f"### 修改 {i+1}\n\n"
            md += f"- **资产**: {entry.get('资产', '')}\n"
            md += f"- **位置**: {entry.get('位置', '')}\n"

            diff = entry.get("diff", {})
            md += f"- **修改前**: {diff.get('before', '')}\n"
            md += f"- **修改后**: {diff.get('after', '')}\n"
            md += f"- **说明**: {entry.get('修改说明', '')}\n\n"

        md += "---\n"
        return md


Editor = EditorAgent
