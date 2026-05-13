"""小哨 TrendScout - 信息采集 Agent (EMP-001)。

v3.0 改造：
- 7 个 mock 文件各抽 3 条 = 21 条
- 统一 LLM 打分（不再有"快速模式"绕过）
- LLM 输出含工作摘要
- 修复 KOC 注入（从 KOC 人设表读取）
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class TrendScoutAgent(BaseAgent):
    """小哨 EMP-001 · 信息官"""

    name = "小哨"
    english_name = "TrendScout"
    emoji = "🛰️"

    MOCK_FILES = [
        "xiaohongshu_hot.json",
        "douyin_hot.json",
        "x_hot.json",
        "hackernews_hot.json",
        "github_trending.json",
        "arxiv_papers.json",
        "reddit_posts.json",
    ]

    SYSTEM_PROMPT = """\
<role>
你是「小哨 TrendScout」，NewsAI 编辑部的信息官。
你的工作是对 21 条来自 7 个平台的 AI 热帖批量打分 + 打标签 + 生成工作摘要。
你不做选题决策（那是小编的事），只做数据预处理。
</role>

<workflow>
1. 阅读 <input> 中的 21 条热帖（每个平台 3 条）
2. 在 <thinking> 里：
   - 整体扫描信息质量分布
   - 思考 KOC 关心的领域有多少条匹配
3. 在 <answer> 输出 JSON，包含：
   - posts: 21 条记录的标签+评分数组
   - log_summary: 本次工作的摘要（写入 LOG 表）
</workflow>

<output_format>
先在 <thinking>...</thinking> 写整体观察（≤150字），
然后 <answer>{完整 JSON}</answer>。
</output_format>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC 人设（v3 修复 P0 Bug：KOC 硬编码）"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            if not koc_record:
                raise RuntimeError(
                    "KOC-001 人设不存在。bootstrap.py 必须先创建 KOC 人设。"
                )
            koc = parse_koc_data(koc_record.data)
            return {"koc": koc}
        except Exception as e:
            print(f"[小哨] 读取 KOC 人设失败: {e}")
            raise

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """读 7 个 mock 文件，每个随机抽 3 条 = 21 条"""
        mock_dir = Path("mock_data")
        all_posts = []

        for filename in self.MOCK_FILES:
            filepath = mock_dir / filename
            if not filepath.exists():
                print(f"[小哨] 警告: mock 文件不存在: {filepath}")
                continue

            try:
                with open(filepath, encoding="utf-8") as f:
                    posts = json.load(f)

                # 随机抽 3 条（如果文件 >= 3 条）
                sampled = random.sample(posts, k=min(3, len(posts)))
                for post in sampled:
                    post["_source_file"] = filename
                all_posts.extend(sampled)
                print(f"[小哨] 从 {filename} 抽取 {len(sampled)} 条")
            except Exception as e:
                print(f"[小哨] 读取 {filename} 失败: {e}")

        if not all_posts:
            raise RuntimeError("没有从任何 mock 文件加载到数据")

        print(f"[小哨] 共采集 {len(all_posts)} 条热帖")
        return {"raw_posts": all_posts}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """统一 LLM 打分（v3 修复：不再有"快速模式"绕过）"""
        koc = upstream_data["koc"]
        raw_posts = tool_results["raw_posts"]

        # 准备输入数据
        posts_for_llm = [
            {
                "index": i,
                "信源平台": _extract_platform(p),
                "原文标题": p.get("标题", p.get("name", p.get("repo", "无标题"))),
                "原文摘要": p.get("摘要", p.get("内容摘要", p.get("description", "")))[:200],
                "原文语言": _detect_language(p),
                "发布时间": p.get("发布时间", ""),
                "原始互动量": p.get("互动量", p.get("stars", p.get("upvotes", 0))),
            }
            for i, p in enumerate(raw_posts)
        ]

        # 构建 prompt
        koc_block = render_koc_block(koc, mode="identity")
        user_content = self._build_user_prompt(koc_block, posts_for_llm)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        # 调用 LLM 带重试
        thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)

        # 校验
        evaluations = answer.get("posts", [])
        if len(evaluations) != len(raw_posts):
            print(f"[小哨] 警告: LLM 返回 {len(evaluations)} 条评分，期望 {len(raw_posts)} 条")

        return {
            "raw_posts": raw_posts,
            "evaluations": evaluations,
            "log_summary": answer.get("log_summary", ""),
        }

    def _build_user_prompt(self, koc_block: str, posts: list) -> str:
        """构建用户 prompt"""
        posts_json = json.dumps(posts, ensure_ascii=False, indent=2)

        return f"""\
{koc_block}

<input>
今日采集的 {len(posts)} 条热帖（来自 7 个平台，每平台 3 条）：

{posts_json}
</input>

<rules>
【热度评分（0-1 浮点数）评估维度】

维度 1 · 信息增量（40% 权重）
- 新发布、新功能、新数据 → 高分（0.7-1.0）
- 老话题新角度 → 中分（0.4-0.6）
- 重复热点 → 低分（0.1-0.3）

维度 2 · KOC 领域匹配度（30%）
- 完全在 KOC 领域内 → 加 0.2
- 部分相关 → 加 0.1
- 无关 → 减 0.3

维度 3 · 传播潜力（30%）
- 有明确"看点"（具体人物/数字/事件） → 高分
- 抽象讨论 → 低分

【内容质量三档】
- "高"：有具体数据、可信来源、第一手消息
- "中"：有观点但缺数据、转述但加了价值
- "低"：标题党、纯转述、营销稿

【主题标签（从固定枚举里选 1-3 个）】
固定枚举：
- "新模型发布"
- "新工具发布"
- "新功能更新"
- "行业八卦"
- "技术突破"
- "实操教程"
- "产品测评"
- "趋势预测"
- "争议事件"
- "其他"

【LOG 工作摘要要求】
- 一句话总结：本次扫描了 N 条，高质量 X 条，匹配 KOC 领域 Y 条
- 异常提示：发现 Z 条触碰 KOC 禁区话题（如有）
- ≤ 100 字
</rules>

<self_check>
输出前确认：
□ posts 数组长度 = 输入数组长度（{len(posts)} 条全打分，不漏一条）
□ 热度评分是 0-1 浮点数，不是 0-10 或百分比
□ 内容质量必须"高/中/低"三选一
□ 主题标签从固定枚举里选 1-3 个，不自创
□ 评分理由 ≤ 50 字
□ log_summary ≤ 100 字
□ 每条记录都有 index 字段对应输入
</self_check>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """写入 TREND 表"""
        raw_posts = result["raw_posts"]
        evaluations = result.get("evaluations", [])

        # 按 index 匹配评分结果
        eval_by_index = {e.get("index", i): e for i, e in enumerate(evaluations)}

        trend_ids = []
        for i, post in enumerate(raw_posts):
            evaluation = eval_by_index.get(i, {
                "热度评分": 0.5,
                "内容质量": "中",
                "主题标签": ["其他"],
            })

            trend_id = IDGenerator.generate("TREND")

            # 处理发布时间：字符串 → 毫秒时间戳
            pub_time_raw = post.get("发布时间", "")
            pub_ts = current_timestamp_ms()  # 默认当前时间
            if pub_time_raw and isinstance(pub_time_raw, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(pub_time_raw.replace('Z', '+00:00').replace('/', '-'))
                    pub_ts = int(dt.timestamp() * 1000)
                except Exception:
                    pass

            record = {
                "id": trend_id,
                "信源ID": post.get("_source_file", "unknown"),
                "信源平台": _extract_platform(post),
                "标题": post.get("标题", post.get("name", post.get("repo", "无标题"))),
                "原文链接": post.get("原文链接", post.get("链接", post.get("hn链接", post.get("pdf链接", "")))),
                "原文摘要": post.get("摘要", post.get("内容摘要", post.get("description", "")))[:500],
                "原文语言": _detect_language(post),
                "主题标签": evaluation.get("主题标签", ["其他"]),
                "阅览量": post.get("阅览量", post.get("views", 0)),
                "互动量": post.get("互动量", post.get("stars", post.get("upvotes", 0))),
                "发布时间": pub_ts,
                "抓取时间": current_timestamp_ms(),
                "热度评分": evaluation.get("热度评分", 0.5),
                "内容质量": evaluation.get("内容质量", "中"),
                "状态": "待选",
            }
            try:
                self.storage.create("热帖库", record)
                trend_ids.append(trend_id)
                print(f"[小哨] 写入热帖: {record['标题'][:30]}...")
            except Exception as e:
                print(f"[小哨] 写入热帖失败: {e}")

        result["trend_ids"] = trend_ids
        print(f"[小哨] 完成: 写入 {len(trend_ids)} 条热帖")


# =============================================================================
# 辅助函数
# =============================================================================

def _extract_platform(post: dict) -> str:
    """从 post 中提取平台名称"""
    if "_source_file" in post:
        filename = post["_source_file"]
        mapping = {
            "xiaohongshu_hot.json": "小红书",
            "douyin_hot.json": "抖音",
            "x_hot.json": "X/Twitter",
            "hackernews_hot.json": "HackerNews",
            "github_trending.json": "GitHub",
            "arxiv_papers.json": "arXiv",
            "reddit_posts.json": "Reddit",
        }
        return mapping.get(filename, filename)
    return post.get("信源平台", "未知")


def _detect_language(post: dict) -> str:
    """检测原文语言"""
    source = post.get("_source_file", "")
    if any(x in source for x in ["xiaohongshu", "douyin"]):
        return "中文"
    return "英文"


TrendScout = TrendScoutAgent
