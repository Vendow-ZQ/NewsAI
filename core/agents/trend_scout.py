"""小哨 -- 信息采集 Agent (TrendScout)。
SYSTEM_PROMPT = """
\
<role>
你是「小哨 TrendScout」，NewsAI 编辑部的信息官。
你的工作是：对从全球信息源抓回来的原始 AI 热帖，做结构化的初步评估。
你不做选题决策（那是小编的事），你只做数据预处理和打分。
</role>

<workflow>
1. 阅读 <input> 中的一条热帖（标题 + 摘要 + 来源）
2. 在 <thinking> 里思考：
   - 这条信息对 KOC【{koc_account}】的领域是否相关？
   - 这条信息的"信息密度"高不高？（有实质内容 vs 标题党）
   - 这条信息属于什么主题分类？
3. 在 <answer> 输出 JSON
</workflow>

<output_format>
先在 <thinking>...</thinking> 里思考（≤100字），
然后在 <answer>{...}</answer> 里输出 JSON。
</output_format>
"""


小哨是NewsAI的信息官，负责：
1. 从多个信息源抓取最新AI动态
2. 使用LLM进行热度评分和标签提取
3. 将处理后的热帖写入热帖池
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from core.sources import get_source


class TrendScoutAgent(BaseAgent):
    """小哨 TrendScout - 信息官。

    负责信息采集、热度评分、标签提取。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小哨", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取信源配置。

        从"信源配置"表中读取所有启用的信源。
        """
        try:
            # 使用 storage.query 查询启用的信源
            from core.storage.interface import QueryFilter
            filters = [QueryFilter(field="是否启用", operator="eq", value=True)]
            sources = self.storage.query("信源配置", filters=filters, limit=100)
            return {"sources": [s.data for s in sources]}
        except Exception as e:
            print(f"[小哨] 读取信源配置失败: {e}")
            return {"sources": []}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """抓取信息源（MOCK模式）。

        直接返回mock热帖数据，不调用真实爬虫。
        """
        mock_items = [
            {
                "标题": "OpenAI发布GPT-5预览版，多模态能力大幅提升",
                "原文摘要": "OpenAI今日正式发布GPT-5预览版本，新模型在图像理解、视频生成和多语言处理方面实现突破性进展。据官方介绍，GPT-5的推理能力较前代提升40%，支持长达100万token的上下文窗口。",
                "原文链接": "https://example.com/news/1",
                "信源平台": "MOCK-科技资讯",
                "信源ID": "mock-001",
                "抓取时间": datetime.now().isoformat(),
            },
            {
                "标题": "Anthropic推出Claude 4.6：编程能力超越GPT-4",
                "原文摘要": "Anthropic发布新一代大模型Claude 4.6，在SWE-bench编程基准测试中创下新纪录。新模型支持更长的思维链，在复杂代码重构和bug修复任务上表现优异。",
                "原文链接": "https://example.com/news/2",
                "信源平台": "MOCK-AI动态",
                "信源ID": "mock-002",
                "抓取时间": datetime.now().isoformat(),
            },
            {
                "标题": "Google Gemini 2.0震撼登场，原生多模态引领行业",
                "原文摘要": "Google DeepMind发布Gemini 2.0系列模型，首次实现真正意义上的原生多模态理解。模型可同时处理文本、图像、音频、视频输入，并生成任意模态输出。",
                "原文链接": "https://example.com/news/3",
                "信源平台": "MOCK-科技资讯",
                "信源ID": "mock-003",
                "抓取时间": datetime.now().isoformat(),
            },
            {
                "标题": "马斯克xAI完成新一轮融资，估值突破500亿美元",
                "原文摘要": "埃隆·马斯克旗下人工智能公司xAI宣布完成60亿美元C轮融资，公司估值达到500亿美元。本轮融资将用于加速Grok模型训练和建设超级算力集群。",
                "原文链接": "https://example.com/news/4",
                "信源平台": "MOCK-财经科技",
                "信源ID": "mock-004",
                "抓取时间": datetime.now().isoformat(),
            },
            {
                "标题": "Midjourney V7发布：AI绘画进入实时生成时代",
                "原文摘要": "Midjourney正式发布V7版本，引入实时画布功能，用户可通过简单涂鸦实时生成高质量图像。新版本还支持风格迁移和角色一致性控制，创作效率提升10倍。",
                "原文链接": "https://example.com/news/5",
                "信源平台": "MOCK-AI工具",
                "信源ID": "mock-005",
                "抓取时间": datetime.now().isoformat(),
            },
        ]

        print(f"[小哨] MOCK模式：返回 {len(mock_items)} 条热帖")
        return {"items": mock_items}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM打标签+评分。

        对每条抓取的信息，使用LLM进行：
        - 热度评分 (0-1)
        - 内容质量评估 (高/中/低)
        - 主题标签提取
        """
        items = tool_results.get("items", [])
        koc = context.get("koc", {})

        for item in items:
            prompt = self._build_analysis_prompt(item, koc)
            try:
                response = self.llm.invoke(prompt)
                analysis = self._parse_llm_response(response)
                item["热度评分"] = analysis.get("热度评分", 0.5)
                item["内容质量"] = analysis.get("内容质量", "中")
                item["主题标签"] = analysis.get("主题标签", [])
            except Exception as e:
                print(f"[小哨] LLM分析失败: {e}")
                item["热度评分"] = 0.5
                item["内容质量"] = "中"
                item["主题标签"] = []

        return {"items": items, "count": len(items)}

    def _build_analysis_prompt(self, item: dict, koc: dict) -> str:
        """构建LLM分析提示词。"""
        return f"""分析以下AI信息，给出热度评分(0-1)和主题标签。

信息标题：{item.get('标题', item.get('title', ''))}
信息摘要：{item.get('原文摘要', item.get('summary', ''))[:500]}
信源平台：{item.get('信源平台', '')}

KOC人设的偏好领域：{koc.get('领域', [])}

请返回JSON格式：
{{"热度评分": 0.5, "内容质量": "高", "主题标签": ["AI", "大模型"]}}

注意：
- 热度评分：0-1之间的小数，1表示极高热度
- 内容质量：高/中/低三档
- 主题标签：2-4个关键词标签
"""

    def _parse_llm_response(self, response: Any) -> dict:
        """解析LLM响应。"""
        try:
            # 尝试直接解析JSON
            if isinstance(response, str):
                return json.loads(response)
            # LangChain消息对象
            if hasattr(response, 'content'):
                content = response.content
                # 尝试从markdown代码块中提取JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                return json.loads(content.strip())
            return {}
        except Exception as e:
            print(f"[小哨] 解析LLM响应失败: {e}")
            return {}

    def _write_storage(self, context: dict, result: dict):
        """写入热帖池。

        将处理后的热帖写入"热帖池"表。
        """
        items = result.get("items", [])
        from core.storage.id_generator import IDGenerator

        for item in items:
            business_id = IDGenerator.generate("TREND")
            record_data = {
                "id": business_id,
                "标题": item.get("标题", item.get("title", "")),
                
                "原文摘要": item.get("原文摘要", item.get("summary", "")),
                "信源平台": item.get("信源平台", ""),
                "信源ID": item.get("信源ID", ""),
                "热度评分": item.get("热度评分", 0.5),
                "内容质量": item.get("内容质量", "中"),
                "主题标签": item.get("主题标签", []),
                "状态": "待选",
                
            }
            try:
                self.storage.create("热帖库", record_data)
            except Exception as e:
                print(f"[小哨] 写入热帖库失败: {e}")

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小哨] 完成：抓取 {count} 条热帖")
        # 调用父类的日志方法
        super()._log_work(context, result)


# 保持向后兼容的别名
TrendScout = TrendScoutAgent
