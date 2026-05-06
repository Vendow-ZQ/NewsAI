"""小图 -- 视觉设计 Agent (VisualDesigner)。
SYSTEM_PROMPT = """
\
<role>
你是「小图 VisualDesigner」，NewsAI 编辑部的视觉设计师，生产组成员。
你的工作是：读小文写好的帖子文档里的 [配图N: 描述]，
为每个配图生成"3 选 1"的设计方案：
1. 文字卡片图（HTML 模板渲染，最常用）
2. 信息图（SVG 模板，对比/流程类）
3. AI 画面图（即梦 prompt，需要画面感时用）
</role>

<workflow>
1. 读 <input> 的选题 + 帖子文档的配图说明列表
2. 在 <thinking> 里：
   - 每张图最适合哪种类型？（文字卡片 / 信息图 / AI 画面）
   - 为什么这种类型最适合？
3. 在 <answer> 输出每张图的设计方案
</workflow>

<output_format>
先在 <thinking>...</thinking>，
然后在 <answer>{...}</answer>。
</output_format>
"""


小图是NewsAI的视觉设计师，负责：
1. 读取选题库中状态="生产中"的选题
2. 读取帖子内容（小文已生成）
3. 分析内容，生成配图方案
4. 更新选题库：配图方案字段

生成内容：
- 文字卡片图描述（HTML模板建议）
- 信息图描述（SVG模板建议）
- AI生图prompt（即梦API用）
- 配图与正文对应关系
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from core.storage.interface import QueryFilter


class VisualDesignerAgent(BaseAgent):
    """小图 VisualDesigner - 视觉设计师。

    负责配图方案设计：文字卡片、信息图、AI画面图。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小图", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中状态="已选"的选题及帖子内容。

        从"选题库"表中读取状态为"已选"的选题（小编创建后的状态），
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
                # 查询所有"已选"状态的选题（小编创建后的状态）
                filters = [QueryFilter(field="状态", operator="eq", value="已选")]
                records = self.storage.query("选题库", filters=filters, limit=10)
                topics = [r.data for r in records]

            return {
                "koc": koc,
                "topics": topics,
            }
        except Exception as e:
            print(f"[小图] 读取上游数据失败: {e}")
            return {"koc": {}, "topics": []}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小图暂不需要调用外部工具，配图生成由后续步骤处理。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """调用LLM生成配图方案。

        为每个选题分析内容，生成完整的配图方案：
        - 文字卡片图描述
        - 信息图描述
        - AI生图prompt
        - 配图与正文对应关系
        """
        topics = upstream_data.get("topics", [])
        koc = upstream_data.get("koc", {})

        results = []
        for topic in topics:
            prompt = self._build_design_prompt(topic, koc)
            try:
                response = self.llm.invoke(prompt)
                design_plan = self._parse_llm_response(response)
                results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "配图方案": design_plan.get("配图方案", []),
                    "视觉风格": design_plan.get("视觉风格", ""),
                })
            except Exception as e:
                print(f"[小图] LLM生成配图方案失败: {e}")
                results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "配图方案": [],
                    "视觉风格": "",
                    "error": str(e),
                })

        return {"designs": results, "count": len(results)}

    def _build_design_prompt(self, topic: dict, koc: dict) -> str:
        """构建配图方案设计的LLM提示词。"""
        koc_name = koc.get("KOC名称", "学AI的刘同学")
        koc_style = koc.get("视觉风格", "简洁科技风，蓝白配色")

        topic_title = topic.get("选题标题", "")
        topic_angle = topic.get("选题角度", "")
        key_points = topic.get("预估爆点", "")
        post_doc_url = topic.get("帖子文档链接", "")

        return f"""你是【小图 VisualDesigner】，为 KOC【{koc_name}】工作。

KOC视觉风格偏好：{koc_style}

请为以下内容设计配图方案：

选题：{topic_title}
选题角度：{topic_angle}
预估爆点：{key_points}
帖子文档链接：{post_doc_url if post_doc_url else "（待生成）"}
（内容已写入飞书云文档，根据选题角度和预估爆点设计配图即可）

请返回JSON格式：
{{
  "配图方案": [
    {{
      "配图编号": "配图1",
      "用途": "公众号封面/小红书首图/正文插图",
      "类型": "文字卡片/信息图/AI画面图",
      "描述": "画面描述...",
      "技术方案": "HTML模板名/SVG模板名/即梦API",
      "AI生成Prompt": "即梦API用的prompt（如适用）...",
      "对应正文位置": "第X段/封面/首图"
    }},
    ...
  ],
  "视觉风格": "整体风格建议"
}}

配图类型说明：
1. 文字卡片：适合金句、核心观点，用HTML模板渲染
2. 信息图：适合数据、流程、对比，用SVG模板渲染
3. AI画面图：适合场景图、概念图，用即梦API生成

要求：
- 每篇内容配3-5张图
- 封面图必须吸引人
- 正文插图与内容紧密对应
- AI生成Prompt要详细，包含风格、构图、色彩"""

    def _parse_llm_response(self, response: Any) -> dict:
        """解析LLM响应为配图方案。"""
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
            print(f"[小图] 解析LLM响应失败: {e}")
            return {"配图方案": [], "视觉风格": ""}

    def _write_storage(self, context: dict, result: dict):
        """将配图方案写入选题库。

        更新选题库中对应选题的"配图方案"字段。
        """
        designs = result.get("designs", [])

        for design in designs:
            topic_id = design.get("topic_id")
            if not topic_id:
                continue

            update_data = {
                "配图方案": json.dumps(design.get("配图方案", []), ensure_ascii=False),
                "视觉风格": design.get("视觉风格", ""),
                "配图更新时间": int(datetime.now().timestamp() * 1000),
            }

            try:
                self.storage.update("选题库", topic_id, update_data)
                print(f"[小图] 已更新选题 {topic_id} 的配图方案")
            except Exception as e:
                print(f"[小图] 更新选题 {topic_id} 失败: {e}")

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小图] 完成：为 {count} 个选题生成配图方案")
        super()._log_work(context, result)


# 保持向后兼容的别名
VisualDesigner = VisualDesignerAgent
