"""小播 -- 短视频编剧 Agent (ScriptWriter)。

小播是NewsAI的短视频编剧，负责：
1. 读取选题库中状态="已选"的选题
2. 读取帖子内容
3. 用LLM生成视频脚本（抖音30-60秒 + B站1-3分钟）
4. 创建飞书云文档（[脚本] {date} {title}）
5. 将文档URL回填到选题库"视频脚本文档链接"字段

生成内容：
- 抖音版脚本（30-60秒）
- B站版脚本（1-3分钟）
- 分镜清单
- BGM建议
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from core.storage.interface import QueryFilter
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage


class ScriptWriterAgent(BaseAgent):
    """小播 ScriptWriter - 短视频编剧。

    负责生成抖音和B站视频脚本。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小播", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中状态="已选"的选题。

        从"选题库"表中读取状态为"生产中"的选题，
        同时读取KOC人设信息。
        """
        topic_id = context.get("topic_id")
        koc_id = context.get("koc_id", "KOC-001")

        try:
            # 读取KOC人设
            koc_record = self.storage.get_by_id("KOC人设", koc_id)
            koc = koc_record.data if koc_record else {}

            # 读取选题
            if topic_id:
                topic_record = self.storage.get_by_id("选题库", topic_id)
                topics = [topic_record.data] if topic_record else []
            else:
                # 查询所有"生产中"或"审改中"状态的选题（手动过滤避免QueryFilter问题）
                all_records = self.storage.query("选题库", limit=100)
                valid_status = ["生产中", "审改中"]
                topics = [r.data for r in all_records if r.data.get("状态") in valid_status][:10]

            return {
                "koc": koc,
                "topics": topics,
            }
        except Exception as e:
            print(f"[小播] 读取上游数据失败: {e}")
            return {"koc": {}, "topics": []}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小播暂不需要调用外部工具。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """调用LLM生成视频脚本。

        为每个选题生成：
        - 抖音版脚本（30-60秒）
        - B站版脚本（1-3分钟）
        """
        topics = upstream_data.get("topics", [])
        koc = upstream_data.get("koc", {})

        results = []
        for topic in topics:
            prompt = self._build_script_prompt(topic, koc)
            try:
                response = self.llm.invoke(prompt)
                scripts = self._parse_llm_response(response)
                results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "抖音版": scripts.get("抖音版", {}),
                    "B站版": scripts.get("B站版", {}),
                })
            except Exception as e:
                print(f"[小播] LLM生成脚本失败: {e}")
                results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "抖音版": {},
                    "B站版": {},
                    "error": str(e),
                })

        return {"scripts": results, "count": len(results)}

    def _build_script_prompt(self, topic: dict, koc: dict) -> str:
        """构建视频脚本生成的LLM提示词。"""
        koc_name = koc.get("KOC名称", "学AI的刘同学")
        koc_tone = koc.get("语气风格", "专业但接地气，善用比喻")
        koc_platform_strategy = koc.get("平台策略", "抖音重钩子，B站重深度")

        topic_title = topic.get("选题标题", "")
        topic_angle = topic.get("选题角度", "")
        key_points = topic.get("关键信息点", "")
        wechat_content = topic.get("公众号正文", "")

        return f"""你是【小播 ScriptWriter】，为 KOC【{koc_name}】工作。

KOC语气：{koc_tone}
平台策略：{koc_platform_strategy}

请为以下选题撰写视频脚本：

选题：{topic_title}
选题角度：{topic_angle}
关键信息点：{key_points}
参考正文：{wechat_content[:1500] if wechat_content else "（待生成）"}

请返回JSON格式：
{{
  "抖音版": {{
    "时长": "45秒",
    "钩子开场": "0-3秒画面+口播文案",
    "核心内容": "3-40秒分镜脚本，包含画面描述和口播文案",
    "CTA": "40-45秒行动号召",
    "字幕": ["字幕1", "字幕2", "..."],
    "BGM建议": "风格描述，如'轻快电子乐，节奏感强'",
    "镜头清单": [
      {{"时间": "0-3s", "画面": "...", "口播": "...", "字幕": "..."}},
      {{"时间": "3-15s", "画面": "...", "口播": "...", "字幕": "..."}}
    ]
  }},
  "B站版": {{
    "时长": "2分15秒",
    "开场": "0-15秒，吸引注意力的开场",
    "分段": [
      {{"时间段": "15-60秒", "内容": "第一段内容..."}},
      {{"时间段": "60-100秒", "内容": "第二段内容..."}},
      {{"时间段": "100-135秒", "内容": "第三段内容..."}}
    ],
    "结尾": "总结+互动引导",
    "字幕": ["字幕1", "字幕2", "..."],
    "BGM建议": "风格描述，如'沉稳背景乐，科技感'",
    "镜头清单": [
      {{"时间": "0-15s", "画面": "...", "口播": "...", "字幕": "..."}},
      {{"时间": "15-60s", "画面": "...", "口播": "...", "字幕": "..."}}
    ]
  }}
}}

脚本要求：
1. 抖音版：
   - 前3秒必须有强钩子，让人想继续看
   - 节奏快，信息密度高
   - 每15秒一个信息点
   - 结尾有明确的CTA（关注/点赞/评论引导）

2. B站版：
   - 开场15秒建立期待
   - 内容有层次，由浅入深
   - 适合竖屏观看（9:16）
   - 结尾引导互动

3. 统一要求：
   - 口播文案要口语化，适合念出来
   - 画面描述要具体，便于拍摄/剪辑
   - 字幕要简洁，突出关键词"""

    def _parse_llm_response(self, response: Any) -> dict:
        """解析LLM响应为视频脚本。"""
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
            print(f"[小播] 解析LLM响应失败: {e}")
            return {"抖音版": {}, "B站版": {}}

    def _write_storage(self, context: dict, result: dict):
        """创建飞书云文档并回填URL。"""
        scripts = result.get("scripts", [])
        doc_storage = FeishuDocStorage()
        date_str = datetime.now().strftime("%Y%m%d")

        for script in scripts:
            topic_id = script.get("topic_id")
            topic_title = script.get("topic_title", "")
            if not topic_id:
                continue

            script_content = {
                "抖音版": script.get("抖音版", {}),
                "B站版": script.get("B站版", {}),
            }

            try:
                existing = self.storage.get_by_id("选题库", topic_id)
                existing_url = existing.data.get("视频脚本文档链接", "") if existing else ""

                if existing_url:
                    # Handle URL field format - could be dict or string
                    url_str = existing_url.get('link', '') if isinstance(existing_url, dict) else existing_url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ''
                else:
                    doc_id = doc_storage.create_script_doc(topic_title, date_str)

                doc_markdown = self._format_script_document(topic_title, script_content)
                doc_storage.append_section(doc_id, doc_markdown)

                # 设置权限（组织内可查看）
                doc_storage.set_permissions(doc_id, share_type="tenant_readable")
                doc_url = doc_storage.get_share_url(doc_id)

                print(f"[小播] 写入视频脚本: {topic_title[:30]}...")
                print(f"[小播] 文档链接: {doc_url}")

                self.storage.update("选题库", topic_id, {"视频脚本文档链接": doc_url})
            except Exception as e:
                print(f"[小播] 写入脚本失败: {e}")

    def _format_script_document(self, topic_title: str, scripts: dict) -> str:
        """格式化视频脚本为Markdown文档格式。"""
        content = f"# {topic_title} - 视频脚本\n\n"

        # 抖音版
        if "抖音版" in scripts:
            dy = scripts["抖音版"]
            content += "## 抖音版\n\n"
            content += f"**时长**: {dy.get('时长', '45秒')}\n\n"
            content += f"**钩子开场**: {dy.get('钩子开场', '')}\n\n"
            content += f"**核心内容**: {dy.get('核心内容', '')}\n\n"
            if dy.get('CTA'):
                content += f"**CTA**: {dy.get('CTA')}\n\n"
            if dy.get('BGM建议'):
                content += f"*BGM*: {dy.get('BGM建议')}\n\n"

        # B站版
        if "B站版" in scripts:
            bz = scripts["B站版"]
            content += "## B站版\n\n"
            content += f"**时长**: {bz.get('时长', '2分15秒')}\n\n"
            content += f"**开场**: {bz.get('开场', '')}\n\n"
            if bz.get('分段'):
                content += "**分段内容**:\n\n"
                for segment in bz['分段']:
                    content += f"- {segment.get('时间段', '')}: {segment.get('内容', '')}\n"
                content += "\n"
            if bz.get('结尾'):
                content += f"**结尾**: {bz.get('结尾')}\n\n"
            if bz.get('BGM建议'):
                content += f"*BGM*: {bz.get('BGM建议')}\n\n"

        return content

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小播] 完成：为 {count} 个选题生成视频脚本")
        super()._log_work(context, result)


# 保持向后兼容的别名
ScriptWriter = ScriptWriterAgent
