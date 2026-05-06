"""小改 Editor -- 编辑 Agent (EMP-007)。

小改是NewsAI治理组的编辑，负责：
1. 读取选题库中状态="审改中"的选题
2. 读取审改记录（获取最新审查意见）
3. 调用LLM生成修改后的内容
4. 更新选题库：帖子内容/视频脚本内容 + 审改记录追加修改日志
5. 审改轮次不变，等待小审再次审查

审改循环逻辑：
- 小审发现问题 → 状态="审改中"
- 小改修改内容 → 状态保持"审改中"，追加修改记录
- 等待小审再次审查
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


class EditorAgent(BaseAgent):
    """小改 Editor - 编辑。

    负责根据审改意见修改内容，优化质量。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小改", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中"审改中"状态的选题。

        从"选题库"表中读取状态为"审改中"的选题，
        并读取相关的审改记录。
        """
        try:
            from core.storage.interface import QueryFilter

            # 读取审改中的选题（手动过滤避免QueryFilter问题）
            all_topics = self.storage.query("选题库", limit=100)
            topics = [t for t in all_topics if t.data.get("状态") == "审改中"][:10]

            # 获取KOC人设
            koc = self._load_koc(context.get("koc_id", "KOC-001"))

            return {
                "topics": [t.data for t in topics],
                "koc": koc
            }
        except Exception as e:
            print(f"[小改] 读取选题库失败: {e}")
            return {"topics": [], "koc": {}}

    def _load_koc(self, koc_id: str) -> dict:
        """加载KOC人设。"""
        try:
            record = self.storage.get_by_id("KOC人设", koc_id)
            return record.data if record else {}
        except Exception as e:
            print(f"[小改] 加载KOC人设失败: {e}")
            return {}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小改不需要调用外部工具，直接返回空结果。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM修改内容。

        对每个选题，根据审改记录中的意见进行修改：
        - 分析审改记录中的问题
        - 生成修改后的帖子内容
        - 生成修改后的视频脚本内容
        """
        topics = upstream_data.get("topics", [])
        koc = upstream_data.get("koc", {})

        # 初始化文档存储（用于读取文档内容）
        doc_storage = FeishuDocStorage()

        edit_results = []
        for topic in topics:
            # 获取文档链接（从URL字段读取）
            post_url = topic.get("帖子文档链接", "")
            script_url = topic.get("视频脚本文档链接", "")

            # 检查是否有审改文档
            audit_url = topic.get("审改文档链接", "")
            if not audit_url:
                print(f"[小改] 选题 {topic.get('id', '')} 无审改文档，跳过")
                continue

            # 从URL读取文档内容
            posts = {}
            scripts = {}

            if post_url:
                try:
                    doc_id = doc_storage.extract_doc_id_from_url(post_url)
                    post_content = doc_storage.read_doc_content(doc_id)
                    posts = {"文档内容": post_content[:2000]} if post_content else {}
                except Exception as e:
                    print(f"[小改] 读取帖子文档失败: {e}")
                    posts = {"链接": post_url}

            if script_url:
                try:
                    doc_id = doc_storage.extract_doc_id_from_url(script_url)
                    script_content = doc_storage.read_doc_content(doc_id)
                    scripts = {"文档内容": script_content[:2000]} if script_content else {}
                except Exception as e:
                    print(f"[小改] 读取脚本文档失败: {e}")
                    scripts = {"链接": script_url}

            # 构建修改提示词（简化版，不传递完整审改记录文本）
            prompt = self._build_edit_prompt(topic, posts, scripts, "审改意见见飞书审改文档", koc)

            try:
                response = self.llm.invoke(prompt)
                edit_result = self._parse_llm_response(response)

                edit_results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "edit_result": edit_result,
                    "original_posts": posts,
                    "original_scripts": scripts,
                })
            except Exception as e:
                print(f"[小改] LLM修改失败: {e}")

        return {"edit_results": edit_results, "count": len(edit_results)}

    def _build_edit_prompt(self, topic: dict, posts: dict, scripts: dict,
                          review_record: str, koc: dict) -> str:
        """构建修改提示词。"""
        # 提取KOC相关字段
        koc_name = koc.get("账号名", "学AI的刘同学")
        koc_tone = koc.get("语气", "玩梗活泼 + 专业硬核")
        koc_structure = koc.get("偏爱内容结构", "反转开头、对比清单、实操步骤流、干货合集")
        koc_platform_strategy = koc.get("平台差异化策略", "")

        # 格式化帖子内容
        post_text = json.dumps(posts, ensure_ascii=False, indent=2) if posts else "无"
        script_text = json.dumps(scripts, ensure_ascii=False, indent=2) if scripts else "无"

        return f"""你是【小改 Editor】，为KOC【{koc_name}】修改内容。

KOC语气基调：
{koc_tone}

KOC偏爱内容结构：
{koc_structure}

KOC平台差异化策略：
{koc_platform_strategy}

请根据以下审改意见修改内容：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}

原始帖子内容：
{post_text}

原始视频脚本：
{script_text}

审改记录（审查意见）：
{review_record}

请返回JSON格式：
{{
  "修改总结": "简要说明修改了哪些内容",
  "修改后的帖子内容": {{
    "公众号": "修改后的公众号文章内容",
    "小红书": "修改后的小红书笔记内容",
    "抖音": "修改后的抖音文案",
    "B站": "修改后的B站专栏内容"
  }},
  "修改后的视频脚本": {{
    "抖音": "修改后的抖音视频脚本",
    "B站": "修改后的B站视频脚本"
  }},
  "修改说明": [
    {{"位置": "公众号第2段", "修改": "具体修改内容", "原因": "对应审查意见"}},
    {{"位置": "小红书标题", "修改": "具体修改内容", "原因": "对应审查意见"}}
  ]
}}

修改原则：
1. 严格对照审查意见中的问题进行修改
2. 保持KOC的语气基调和风格一致性
3. 保持平台差异化策略（公众号深度、小红书图文、抖音钩子、B站教程）
4. 不引入新的风险词或合规问题
5. 确保修改后的内容比原文更优质

注意：
- 如果审查意见指出事实错误，必须核实并修正
- 如果审查意见指出风格偏差，必须调整语气
- 如果审查意见指出合规风险，必须彻底移除风险内容
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
            print(f"[小改] 解析LLM响应失败: {e}")
            return {
                "修改总结": "解析失败",
                "修改后的帖子内容": {},
                "修改后的视频脚本": {},
                "修改说明": [{"位置": "解析失败", "修改": "无法解析LLM响应", "原因": "请人工检查"}]
            }

    def _write_storage(self, context: dict, result: dict):
        """追加修改章节到审改云文档。

        状态保持"审改中"（等待小审再次审查）

        防循环保护：如果没有可修改的内容，直接标记为"待发布"防止无限循环。
        """
        edit_results = result.get("edit_results", [])
        doc_storage = FeishuDocStorage()

        # 防循环保护：如果没有修改结果，直接通过
        if not edit_results:
            print(f"[小改] 警告：无修改内容，强制通过防止循环")
            try:
                # 手动过滤避免QueryFilter问题
                all_topics = self.storage.query("选题库", limit=100)
                topics = [t for t in all_topics if t.data.get("状态") == "审改中"][:10]
                for topic in topics:
                    topic_id = topic.data.get("id", "")
                    topic_title = topic.data.get("选题标题", "")
                    if topic_id:
                        # 读取已有审改文档并追加强制通过记录
                        existing_url = topic.data.get("审改文档链接", "")
                        if existing_url:
                            # Handle URL field format - could be dict or string
                            url_str = existing_url.get('link', '') if isinstance(existing_url, dict) else existing_url
                            doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                            force_pass_entry = f"\n## 强制通过\n\n小改无修改内容，强制通过防止无限循环。\n\n"
                            doc_storage.append_section(doc_id, force_pass_entry)
                        self.storage.update("选题库", topic_id, {"状态": "待发布"})
                        print(f"[小改] 强制通过：{topic_id}")
            except Exception as e:
                print(f"[小改] 强制通过失败: {e}")
            return

        for edit in edit_results:
            topic_id = edit.get("topic_id", "")
            topic_title = edit.get("topic_title", "")
            edit_data = edit.get("edit_result", {})

            edit_summary = edit_data.get("修改总结", "")
            edit_details = edit_data.get("修改说明", [])

            try:
                # 读取已有审改文档链接
                existing = self.storage.get_by_id("选题库", topic_id)
                existing_url = existing.data.get("审改文档链接", "") if existing else ""
                if not existing_url:
                    print(f"[小改] 警告：选题 {topic_id} 无审改文档链接，跳过")
                    continue

                # Handle URL field format - could be dict or string
                url_str = existing_url.get('link', '') if isinstance(existing_url, dict) else existing_url
                doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''

                # 生成修改记录并追加
                edit_entry = self._format_edit_entry(topic_title, edit_summary, edit_details)
                doc_storage.append_section(doc_id, edit_entry)

                # 修改完成后，将状态改回"生产中"，以便小审重新审查
                self.storage.update("选题库", topic_id, {"状态": "生产中"})

                print(f"[小改] 修改完成：{topic_title[:30]}... 修改点：{len(edit_details)}处，状态已重置为'生产中'等待再审")
            except Exception as e:
                print(f"[小改] 更新审改文档失败: {e}")

    def _format_edit_entry(self, topic_title: str, edit_summary: str, edit_details: list) -> str:
        """格式化修改记录条目（Markdown格式）。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        entry = f"""# {topic_title}

## 修改记录 ({now})

**修改总结**: {edit_summary}

### 具体修改
"""

        if edit_details:
            for detail in edit_details:
                entry += f"- **{detail.get('位置', '未知位置')}**: {detail.get('修改', '')}\n"
                entry += f"  - 原因: {detail.get('原因', '')}\n"
        else:
            entry += "- 无详细修改记录\n"

        entry += "\n---\n"
        return entry

    def _format_post_document(self, posts: dict) -> str:
        """格式化帖子内容为Markdown文档。"""
        content = "# 修改后的帖子内容\n\n"

        for platform, post in posts.items():
            content += f"## {platform}版本\n\n"
            if isinstance(post, dict):
                for key, value in post.items():
                    content += f"**{key}**: {value}\n\n"
            else:
                content += f"{post}\n\n"

        return content

    def _format_script_document(self, scripts: dict) -> str:
        """格式化视频脚本为Markdown文档。"""
        content = "# 修改后的视频脚本\n\n"

        for platform, script in scripts.items():
            content += f"## {platform}版\n\n"
            if isinstance(script, dict):
                for key, value in script.items():
                    content += f"**{key}**: {value}\n\n"
            else:
                content += f"{script}\n\n"

        return content

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小改] 完成：修改 {count} 条选题")
        super()._log_work(context, result)


# 保持向后兼容的别名
Editor = EditorAgent
