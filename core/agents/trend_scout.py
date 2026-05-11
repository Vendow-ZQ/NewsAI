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
                    items = items[:2] if len(items) > 2 else items
                    for item in items:
                        title = item.get("标题") or item.get("title") or item.get("热帖标题") or item.get("name") or item.get("repo") or "无标题"
                        summary = item.get("原文摘要") or item.get("summary") or item.get("内容摘要") or item.get("description") or ""
                        link = item.get("原文链接") or item.get("link") or item.get("原始链接") or item.get("url") or ""
                        item_id = hashlib.md5(f"{source_name}:{title}".encode()).hexdigest()[:8]

                        # 统一提取各信源的共性字段
                        pub_time = item.get("发布时间", "")
                        if pub_time and isinstance(pub_time, str) and len(pub_time) <= 10:
                            pub_time = f"{pub_time}T12:00:00"

                        # 阅览量：各平台字段名不同
                        views = item.get("阅览量") or item.get("stars") or item.get("分数") or item.get("upvotes") or 0
                        # 互动量：各平台字段名不同
                        engagement = item.get("互动量")
                        if engagement is None:
                            engagement = (item.get("评论数", 0) or 0) + (item.get("今日新增", 0) or 0)
                        # 原文语言
                        lang = item.get("原文语言", "")
                        if not lang:
                            lang = "英文" if source_name in ["arXiv", "HackerNews", "GitHub", "Reddit", "X/Twitter"] else "中文"
                        # 主题标签
                        tags = item.get("主题标签", [])
                        if not tags and item.get("关键词"):
                            tags = item.get("关键词", [])

                        mock_items.append({
                            "标题": title,
                            "原文摘要": summary[:500] if summary else "暂无摘要",
                            "原文链接": link,
                            "原文语言": lang,
                            "信源平台": source_name,
                            "信源ID": f"{source_name.lower()}-{item_id}",
                            "主题标签": tags if tags else [],
                            "阅览量": int(views) if views else 0,
                            "互动量": int(engagement) if engagement else 0,
                            "发布时间": pub_time or datetime.now().isoformat(),
                            "抓取时间": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
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
        """LLM批量打标签+评分——一次性处理所有热帖，减少API调用次数。"""
        items = tool_results.get("items", [])
        koc = context.get("koc", {})

        if not items:
            return {"items": [], "count": 0}

        # 快速模式：如果mock数据已有主题标签，跳过LLM直接复用
        has_existing_tags = all(item.get("主题标签") for item in items)
        if has_existing_tags:
            print(f"[小哨] 快速模式: 复用mock数据标签，跳过LLM ({len(items)}条)")
            for item in items:
                item["热度评分"] = item.get("热度评分", 0.5) or 0.5
                item["内容质量"] = item.get("内容质量", "中") or "中"
                # 主题标签已存在
            return {"items": items, "count": len(items)}

        # 批量分析：一次性把所有热帖传给LLM
        prompt = self._build_batch_analysis_prompt(items)
        try:
            response = self.llm.invoke(prompt)
            analyses = self._parse_batch_llm_response(response)

            # 将分析结果匹配回热帖
            for i, item in enumerate(items):
                if i < len(analyses):
                    analysis = analyses[i]
                    item["热度评分"] = analysis.get("热度评分", 0.5)
                    item["内容质量"] = analysis.get("内容质量", "中")
                    item["主题标签"] = analysis.get("主题标签", item.get("主题标签", []))
                else:
                    item["热度评分"] = 0.5
                    item["内容质量"] = "中"
                    item["主题标签"] = item.get("主题标签", [])

            print(f"[小哨] 批量LLM分析完成: {len(items)} 条热帖 (1次API调用)")
        except Exception as e:
            print(f"[小哨] 批量LLM分析失败: {e}，使用默认值")
            for item in items:
                item["热度评分"] = 0.5
                item["内容质量"] = "中"
                item["主题标签"] = item.get("主题标签", [])

        return {"items": items, "count": len(items)}

    def _build_batch_analysis_prompt(self, items: list) -> str:
        """构建批量LLM分析提示词——一次性分析多条热帖。"""
        # 构建热帖列表
        item_lines = []
        for i, item in enumerate(items):
            item_lines.append(f"""[{i}]
标题: {item.get('标题', '')}
摘要: {item.get('原文摘要', '')[:50]}
平台: {item.get('信源平台', '')}
""")
        items_text = "\n".join(item_lines)

        return f"""你是AI热帖分析师。请对以下{len(items)}条热帖逐一分析，给出热度评分(0-1)、内容质量(高/中/低)和主题标签。

{items_text}

请返回JSON数组格式：
[
  {{"热度评分": 0.85, "内容质量": "高", "主题标签": ["AI编程", "VibeCoding"]}},
  {{"热度评分": 0.72, "内容质量": "中", "主题标签": ["AI工具", "效率"]}},
  ...
]

注意：
- 热度评分: 0-1之间的小数
- 内容质量: 高/中/低
- 主题标签: 2-4个关键词
- 必须返回与热帖数量相同的数组项
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

    def _parse_batch_llm_response(self, response: Any) -> list:
        """解析批量LLM响应为列表。"""
        try:
            if isinstance(response, str):
                content = response
            elif hasattr(response, "content"):
                content = response.content
            else:
                return []

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "分析结果" in data:
                return data["分析结果"]
            else:
                return []
        except Exception as e:
            print(f"[小哨] 批量解析失败: {e}")
            return []

    def _write_storage(self, context: dict, result: dict):
        """写入热帖池。"""
        items = result.get("items", [])
        from core.storage.id_generator import IDGenerator
        from core.utils.feishu_base import FeishuBaseManager

        for item in items:
            business_id = IDGenerator.generate("TREND")

            # 发布时间转换为飞书Base毫秒时间戳
            pub_time_raw = item.get("发布时间", "")
            pub_ts = FeishuBaseManager.convert_datetime_to_timestamp(pub_time_raw)

            # 抓取时间转换为飞书Base毫秒时间戳
            crawl_time_raw = item.get("抓取时间", "")
            crawl_ts = FeishuBaseManager.convert_datetime_to_timestamp(crawl_time_raw)

            record_data = {
                "id": business_id,
                "信源ID": item.get("信源ID", ""),
                "信源平台": item.get("信源平台", ""),
                "标题": item.get("标题", ""),
                "原文链接": item.get("原文链接", ""),
                "原文摘要": item.get("原文摘要", ""),
                "原文语言": item.get("原文语言", "中文"),
                "主题标签": item.get("主题标签", []),
                "阅览量": int(item.get("阅览量", 0)),
                "互动量": int(item.get("互动量", 0)),
                "发布时间": pub_ts,
                "抓取时间": crawl_ts,
                "热度评分": item.get("热度评分", 0.5),
                "内容质量": item.get("内容质量", "中"),
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
