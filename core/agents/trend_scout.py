# -*- coding: utf-8 -*-
"""小哨 -- 信息采集 Agent (TrendScout)。"""

SYSTEM_PROMPT = """[角色]
你是小哨 TrendScout，NewsAI 编辑部的信息官。
你的工作是对从全球信息源抓回来的原始 AI 热帖，做结构化的初步评估。
你不做选题决策（那是小编的事），你只做数据预处理和打分。

[工作流程]
1. 阅读 input 中的一条热帖（标题 + 摘要 + 来源）
2. 在 thinking 里思考：
   - 这条信息对 KOC 的领域是否相关？
   - 这条信息的"信息密度"高不高？
   - 这条信息属于什么主题分类？
3. 在 answer 输出 JSON

[输出格式]
先在 thinking... 里思考（小于100字），
然后在 answer{...} 里输出 JSON。
"""

import json
import os
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent


class TrendScoutAgent(BaseAgent):
    """小哨 TrendScout - 信息官。"""

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小哨", storage, llm_client)

    def _read_upstream(self, context: dict):
        """读取信源配置。"""
        try:
            from core.storage.interface import QueryFilter
            filters = [QueryFilter(field="是否启用", operator="eq", value=True)]
            sources = self.storage.query("信源配置", filters=filters, limit=100)
            return {"sources": [s.data for s in sources]}
        except Exception as e:
            print(f"[小哨] 读取信源配置失败: {e}")
            return {"sources": []}

    def _invoke_tools(self, context: dict, upstream_data: dict):
        """抓取信息源（MOCK模式）。从 mock_data/ 目录读取JSON文件。"""
        import hashlib

        mock_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_data")

        mock_files = [
            ("xiaohongshu_hot.json", "小红书"),
            ("douyin_hot.json", "抖音"),
            ("github_trending.json", "GitHub"),
            ("hackernews_hot.json", "HackerNews"),
            ("arxiv_papers.json", "arXiv"),
            ("reddit_posts.json", "Reddit"),
            ("x_hot.json", "X/Twitter"),
        ]

        mock_items = []

        for filename, source_name in mock_files:
            filepath = os.path.join(mock_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    items = data if isinstance(data, list) else [data] if data else []

                    # 确保每个信源只取前20条
                    items = items[:20] if len(items) > 20 else items
                    for item in items:
                        title = item.get("标题") or item.get("title") or item.get("热帖标题") or item.get("name") or item.get("repo") or "无标题"
                        summary = item.get("原文摘要") or item.get("summary") or item.get("内容摘要") or item.get("description") or ""
                        link = item.get("原文链接") or item.get("link") or item.get("原始链接") or item.get("url") or ""
                        item_id = hashlib.md5(f"{source_name}:{title}".encode()).hexdigest()[:8]

                        mock_items.append({
                            "标题": title,
                            "原文摘要": summary[:500] if summary else "暂无摘要",
                            "原文链接": link,
                            "信源平台": source_name,
                            "信源ID": f"{source_name.lower()}-{item_id}",
                            "抓取时间": datetime.now().isoformat(),
                        })

                    print(f"[小哨] 从 {filename} 加载了 {len(items[:20])} 条热帖")
                except Exception as e:
                    print(f"[小哨] 加载 {filename} 失败: {e}")

        if not mock_items:
            print("[小哨] 警告: 没有从mock_data加载到数据")
            mock_items = [{"标题": "默认数据", "原文摘要": "请检查mock_data目录", "原文链接": "", "信源平台": "MOCK", "信源ID": "mock-default", "抓取时间": datetime.now().isoformat()}]

        print(f"[小哨] MOCK模式: 返回 {len(mock_items)} 条热帖")
        return {"items": mock_items}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict):
        """LLM打标签+评分。"""
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

信息标题: {item.get('标题', '')}
信息摘要: {item.get('原文摘要', '')[:500]}
信源平台: {item.get('信源平台', '')}

请返回JSON格式:
{{"热度评分": 0.5, "内容质量": "高", "主题标签": ["AI", "大模型"]}}

注意:
- 热度评分: 0-1之间的小数
- 内容质量: 高/中/低
- 主题标签: 2-4个关键词
"""

    def _parse_llm_response(self, response: Any) -> dict:
        """解析LLM响应。"""
        try:
            if isinstance(response, str):
                content = response
            elif hasattr(response, "content"):
                content = response.content
            else:
                return {}

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"[小哨] 解析失败: {e}")
            return {}

    def _write_storage(self, context: dict, result: dict):
        """写入热帖池。"""
        items = result.get("items", [])
        from core.storage.id_generator import IDGenerator

        for item in items:
            business_id = IDGenerator.generate("TREND")
            record_data = {
                "id": business_id,
                "标题": item.get("标题", ""),
                "原文摘要": item.get("原文摘要", ""),
                "信源平台": item.get("信源平台", ""),
                "信源ID": item.get("信源ID", ""),
                "热度评分": item.get("热度评分", 0.5),
                "内容质量": item.get("内容质量", "中"),
                "主题标签": item.get("主题标签", []),
                "状态": "待选",
            }
            try:
                self.storage.create("热帖库", record_data)
                print(f"[小哨] 写入热帖库: {item.get('标题', '')[:30]}...")
            except Exception as e:
                print(f"[小哨] 写入热帖库失败: {e}")

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小哨] 完成: 抓取 {count} 条热帖")
        super()._log_work(context, result)


TrendScout = TrendScoutAgent
