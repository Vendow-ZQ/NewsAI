"""小文 ContentWriter -- 文字编辑 Agent。
SYSTEM_PROMPT = """
\
<role>
你是「小文 ContentWriter」，NewsAI 编辑部的文字编辑，生产组成员。
你的工作是：根据选题，写出 4 个平台版本的文字内容（公众号 / 小红书 / 抖音 / B站）。
你写完后不再修改——审改循环由小审 + 小改负责。
</role>

<workflow>
1. 读 <input> 中的选题方案（来自小编）和 KOC 人设
2. 在 <thinking> 里规划：
   - 4 平台各自的核心写作策略（受众/字数/调性差异）
   - 钩子设计（标题 + 开头 3 句）
   - 信息密度规划（每 100 字至少 1 个 takeaway）
3. 在 <answer> 输出 4 平台完整文案
</workflow>

<output_format>
先在 <thinking>...</thinking> 里规划（≤200字），
然后在 <answer>{...}</answer> 里输出 4 平台版本 JSON。
</output_format>
"""


小文是NewsAI的文字编辑，负责：
1. 读取选题库中状态="已选"的选题
2. 读取KOC人设
3. 用LLM生成4平台版本（公众号/小红书/抖音/B站）
4. 创建飞书云文档（[帖子] {date} {title}）
5. 将文档URL回填到选题库"帖子文档链接"字段
6. 更新状态="生产中"
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


class ContentWriterAgent(BaseAgent):
    """小文 ContentWriter - 文字编辑。

    负责把选题写成4平台版本的内容，存入独立飞书云文档。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小文", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中"已选"状态的选题。"""
        try:
            from core.storage.interface import QueryFilter
            filters = [QueryFilter(field="状态", operator="eq", value="已选")]
            topics = self.storage.query("选题库", filters=filters, limit=10)
            return {"topics": [t.data for t in topics]}
        except Exception as e:
            print(f"[小文] 读取选题库失败: {e}")
            return {"topics": []}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小文不需要调用外部工具，直接返回空结果。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM生成4平台版本内容。"""
        topics = upstream_data.get("topics", [])
        koc = context.get("koc", {})

        contents = []
        for topic in topics:
            prompt = self._build_writing_prompt(topic, koc)
            try:
                response = self.llm.invoke(prompt)
                platforms_content = self._parse_llm_response(response)

                contents.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "platforms": platforms_content,
                })
            except Exception as e:
                print(f"[小文] LLM生成内容失败: {e}")

        return {"contents": contents, "count": len(contents)}

    def _build_writing_prompt(self, topic: dict, koc: dict) -> str:
        """构建内容撰写提示词。"""
        return f"""你是【小文 ContentWriter】，为 KOC【{koc.get('账号名', '学AI的刘同学')}】工作。

KOC语气：{koc.get('语气', '玩梗活泼 + 专业硬核。让大家学到真东西，不过度渲染焦虑等情绪，注重进步性和互助性——咱们是一起进步的同学，不是被 AI 浪潮抛下的人。')}
中文爆款偏好：{koc.get('中文爆款偏好', '标题前8字必有钩子；善用emoji分段；多用"咱们/我们"，少用"你"；结尾留互动钩子；拒绝标题党')}
平台差异化策略：{koc.get('平台差异化策略', '公众号：深度长文；小红书：图文笔记；抖音：短视频；B站：教程视频')}

请为以下选题撰写4个平台版本：

选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}
预估受众：{topic.get('预估受众', '')}

请返回JSON格式：
{{
  "公众号": {{
    "标题": "...",
    "摘要": "...",
    "正文": "...（1500-3000字）",
    "配图说明": "..."
  }},
  "小红书": {{
    "标题": "...",
    "正文": "...（300-500字）",
    "标签": "#AI #ChatGPT"
  }},
  "抖音": {{
    "文案": "...（30-60秒）",
    "钩子": "...",
    "CTA": "..."
  }},
  "B站": {{
    "标题": "...",
    "简介": "...",
    "正文": "..."
  }}
}}

写作要求：
1. 公众号：深度长文，有目录结构，信息密度高
2. 小红书：标题党+emoji分段，6-9张图的建议
3. 抖音：30-60秒钩子型，开场抓人，一个真知识点，行动CTA
4. B站：1-3分钟教程/评测风格，有节奏感
5. 所有平台保持KOC语气一致，多用"咱们/我们"
6. 标题前8字必须有钩子（数字/反差/提问/身份代入）
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

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"[小文] 解析LLM响应失败: {e}")
            return {
                "公众号": {"标题": "", "摘要": "", "正文": "", "配图说明": ""},
                "小红书": {"标题": "", "正文": "", "标签": ""},
                "抖音": {"文案": "", "钩子": "", "CTA": ""},
                "B站": {"标题": "", "简介": "", "正文": ""},
            }

    def _write_storage(self, context: dict, result: dict):
        """创建飞书云文档并回填URL。"""
        contents = result.get("contents", [])
        doc_storage = FeishuDocStorage()
        date_str = datetime.now().strftime("%Y%m%d")

        for content in contents:
            topic_id = content.get("topic_id", "")
            topic_title = content.get("topic_title", "")
            platforms = content.get("platforms", {})

            try:
                # 检查是否已有文档链接
                existing = self.storage.get_by_id("选题库", topic_id)
                existing_url = existing.data.get("帖子文档链接", "") if existing else ""

                if existing_url:
                    # 已有文档，追加内容（理论上小文只写一次，但做保护）
                    # 从URL中提取 doc_id
                    # Handle URL field format - could be dict {'link': '...', 'text': '...'} or string
                    url_str = existing_url.get('link', '') if isinstance(existing_url, dict) else existing_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                else:
                    # 创建新文档
                    doc_id = doc_storage.create_post_doc(topic_title, date_str)

                # 构建并写入内容
                doc_markdown = self._format_post_document(topic_title, platforms)
                doc_storage.append_section(doc_id, doc_markdown)

                # 设置权限（组织内可查看）并获取分享链接
                doc_storage.set_permissions(doc_id, share_type="tenant_readable")
                doc_url = doc_storage.get_share_url(doc_id)

                print(f"[小文] 写入帖子文档: {topic_title[:30]}...")
                print(f"[小文] 文档链接: {doc_url}")

                # 更新选题库：URL + 状态
                update_data = {
                    "帖子文档链接": doc_url,
                    "状态": "生产中",
                    "生产开始时间": int(datetime.now().timestamp() * 1000),
                }
                self.storage.update("选题库", topic_id, update_data)
            except Exception as e:
                print(f"[小文] 写入文档失败: {e}")
                # 失败时仍然更新状态
                try:
                    self.storage.update("选题库", topic_id, {
                        "状态": "生产中",
                        "生产开始时间": int(datetime.now().timestamp() * 1000),
                    })
                except Exception as e2:
                    print(f"[小文] 更新状态失败: {e2}")

    def _format_post_document(self, topic_title: str, platforms: dict) -> str:
        """格式化帖子内容为Markdown文档格式。"""
        content = f"# {topic_title}\n\n"

        if "公众号" in platforms:
            gzh = platforms["公众号"]
            content += "## 公众号版本\n\n"
            content += f"**标题**: {gzh.get('标题', '')}\n\n"
            content += f"**摘要**: {gzh.get('摘要', '')}\n\n"
            content += f"{gzh.get('正文', '')}\n\n"
            if gzh.get('配图说明'):
                content += f"*配图*: {gzh.get('配图说明')}\n\n"

        if "小红书" in platforms:
            xhs = platforms["小红书"]
            content += "## 小红书版本\n\n"
            content += f"**标题**: {xhs.get('标题', '')}\n\n"
            content += f"{xhs.get('正文', '')}\n\n"
            if xhs.get('标签'):
                content += f"*标签*: {xhs.get('标签')}\n\n"

        if "抖音" in platforms:
            dy = platforms["抖音"]
            content += "## 抖音版本\n\n"
            content += f"**钩子**: {dy.get('钩子', '')}\n\n"
            content += f"{dy.get('文案', '')}\n\n"
            if dy.get('CTA'):
                content += f"*CTA*: {dy.get('CTA')}\n\n"

        if "B站" in platforms:
            bz = platforms["B站"]
            content += "## B站版本\n\n"
            content += f"**标题**: {bz.get('标题', '')}\n\n"
            content += f"**简介**: {bz.get('简介', '')}\n\n"
            content += f"{bz.get('正文', '')}\n\n"

        return content

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小文] 完成：撰写 {count} 条选题的4平台版本")
        super()._log_work(context, result)


# 保持向后兼容的别名
ContentWriter = ContentWriterAgent
