# -*- coding: utf-8 -*-
"""Agent module."""

SYSTEM_PROMPT = """

\

<role>

你是「小编 TopicCurator」，NewsAI 编辑部的选题总编，决策组的 leader。

你直接对 KOC【{koc_account}】负责。

你的工作是：从热帖库挑选有爆点的素材，做多角度爆点拆解，

然后生成符合 KOC 风格的可执行选题。

</role>



<workflow>

1. 读 <input> 中的若干条热帖（已经过小哨打分）

2. 在 <thinking> 里：

   - 第 1 关 · 领域：是否在 KOC 领域白名单内？

   - 第 2 关 · 禁区：是否触碰任何一条 KOC 禁区话题？

   - 第 3 关 · 爆点：能从什么具体角度切，让 KOC 受众觉得值得看？

   - 多角度爆点拆解：从「情绪钩子 / 知识增量 / 身份代入 / 反差 / 时效」

     5 个维度评估

3. 在 <answer> 输出选题方案 JSON

   - 如果通过 → 完整方案

   - 如果拒绝 → is_适合=false + 拒绝理由

</workflow>



<output_format>

先在 <thinking>...</thinking> 里写 3 关筛查 + 5 维度爆点拆解（≤300字），

然后在 <answer>{...}</answer> 里输出 JSON。

</output_format>

"""

import json

from datetime import datetime

from typing import Any



from core.agents.base import BaseAgent

from core.storage.id_generator import IDGenerator





class TopicCuratorAgent(BaseAgent):

    """小编 TopicCurator - 选题总编。



    负责从热帖中筛选选题，评估爆点潜力，生成选题方案。

    """



    def __init__(self, storage: Any, llm_client: Any):

        super().__init__("小编", storage, llm_client)



    def _read_upstream(self, context: dict) -> dict:

        """读取热帖库中"待选"状态的热帖。



        从"热帖库"表中读取状态为"待选"的热帖。

        """

        try:

            from core.storage.interface import QueryFilter

            filters = [QueryFilter(field="状态", operator="eq", value="待选")]

            trends = self.storage.query("热帖库", filters=filters, limit=50)

            return {"trends": [t.data for t in trends]}

        except Exception as e:

            print(f"[小编] 读取热帖库失败: {e}")

            return {"trends": []}



    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:

        """小编不需要调用外部工具，直接返回空结果。"""

        return {}



    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:

        """LLM分析选题潜力。



        对每条热帖，结合KOC人设，使用LLM分析：

        - 是否适合作为选题

        - 选题角度

        - 预估爆点

        - 预估受众

        - 推荐优先级

        """

        trends = upstream_data.get("trends", [])

        koc = context.get("koc", {})

        # 限制最多分析50条热帖（从140条中选）
        trends_to_analyze = trends[:50] if len(trends) > 50 else trends
        print(f"[小编] 从{len(trends)}条热帖中分析前{len(trends_to_analyze)}条，最终选出1条最佳选题...")

        topics = []

        for trend in trends_to_analyze:

            prompt = self._build_analysis_prompt(trend, koc)

            try:

                response = self.llm.invoke(prompt)

                analysis = self._parse_llm_response(response)



                # 只保留适合的选题

                if analysis.get("是否适合", False):

                    topics.append({

                        "热帖ID": trend.get("id", ""),

                        "热帖标题": trend.get("标题", ""),

                        "选题标题": analysis.get("选题标题", ""),

                        "选题角度": analysis.get("选题角度", ""),

                        "预估爆点": analysis.get("预估爆点", ""),

                        "预估受众": analysis.get("预估受众", ""),

                        "推荐优先级": analysis.get("推荐优先级", 5),

                    })

            except Exception as e:

                print(f"[小编] LLM分析失败: {e}")



        return {"topics": topics, "count": len(topics)}



    def _build_analysis_prompt(self, trend: dict, koc: dict) -> str:

        """构建选题分析提示词。"""

        return f"""你是【小编 TopicCurator】，为 KOC【{koc.get('账号名', '学AI的刘同学')}】工作。



KOC定位：{koc.get('一句话定位', '给所有非科班大众看的 AI 资讯与教程速递。')}

目标受众：{koc.get('目标受众', '22-35岁的非技术背景知识工作者')}

偏好选题类型：{koc.get('偏好选题类型', ['新模型发布', '新工具评测', '行业八卦', '实操教程'])}

禁区话题：{koc.get('禁区话题', '政治敏感、引战话题、卖课导流、未经证实的揣测、制造焦虑')}



请分析以下热帖，判断是否适合作为选题：



热帖标题：{trend.get('标题', '')}

热帖摘要：{trend.get('原文摘要', '')[:500]}

信源平台：{trend.get('信源平台', '')}

热度评分：{trend.get('热度评分', 0.5)}



请返回JSON格式：

{{

  "是否适合": true/false,

  "选题标题": "一句话选题（20字内）",

  "选题角度": "从什么角度切入（100字）",

  "预估爆点": "为什么这个选题会爆（100字）",

  "预估受众": "目标受众分析（50字）",

  "推荐优先级": 1-10

}}



注意：

- 是否适合：必须符合KOC人设定位，避开禁区话题

- 选题标题：抓人眼球但拒绝标题党

- 推荐优先级：1-10分，10分为最高优先级

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

            print(f"[小编] 解析LLM响应失败: {e}")

            return {"是否适合": False}



    def _write_storage(self, context: dict, result: dict):

        """写入选题库。



        将生成的选题写入"选题库"表，状态为"待选"，并关联热帖ID。

        """

        topics = result.get("topics", [])



        for topic in topics:

            business_id = IDGenerator.generate("TOPIC")

            record_data = {

                "id": business_id,

                "选题标题": topic.get("选题标题", ""),

                "选题角度": topic.get("选题角度", ""),

                "预估爆点": topic.get("预估爆点", ""),

                "预估受众": topic.get("预估受众", ""),

                "关联热帖IDs": json.dumps([topic.get("热帖ID", "")], ensure_ascii=False),

                "KOC人设ID": context.get("koc_id", "KOC-001"),

                "推荐优先级": topic.get("推荐优先级", 5),

                "状态": "已选",

                "审改轮次": 0,

                "创建时间": int(datetime.now().timestamp() * 1000),

            }

            try:

                self.storage.create("选题库", record_data)

                print(f"[小编] 创建选题: {topic.get('选题标题', '')[:30]}...")

            except Exception as e:

                print(f"[小编] 写入选题库失败: {e}")



    def _log_work(self, context: dict, result: dict):

        """记录工作日志。"""

        count = result.get("count", 0)

        print(f"[小编] 完成：生成 {count} 条选题")

        super()._log_work(context, result)





# 保持向后兼容的别名

TopicCurator = TopicCuratorAgent

