"""小审 Reviewer -- 审核员 Agent (EMP-006)。

小审是NewsAI治理组的审核员，负责：
1. 读取选题库中状态="生产中"的选题
2. 读取帖子内容、视频脚本内容
3. 对照KOC人设进行审查（禁区话题、反面人设、审美准则）
4. 生成审查结论（通过/需修改）
5. 写入选题库：审改记录字段 + 更新状态

审改循环逻辑：
- 发现问题 → 结论="需修改"，状态保持"审改中"
- 无问题 → 结论="通过"，状态改为"待发布"
- 审改记录累积追加到"审改记录"字段（Markdown格式）
- 通过"审改轮次"字段记录循环次数（最多3轮）
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent
from feishu_adapter.doc_storage import get_doc_storage


class ReviewerAgent(BaseAgent):
    """小审 Reviewer - 审核员。

    负责审核内容，守住底线和调性。
    """

    def __init__(self, storage: Any, llm_client: Any):
        super().__init__("小审", storage, llm_client)

    def _read_upstream(self, context: dict) -> dict:
        """读取选题库中"生产中"或"审改中"状态的选题。

        从"选题库"表中读取状态为"生产中"（首次审查）
        或"审改中"（修改后再审）的选题。
        排除已经审查过但小改尚未修改的选题（防止无限循环）。
        """
        try:
            from core.storage.interface import QueryFilter

            # 读取生产中或审改中的选题
            filters = [
                QueryFilter(field="状态", operator="in", value=["生产中", "审改中"])
            ]
            topics = self.storage.query("选题库", filters=filters, limit=10)

            # 过滤掉已经审查过但尚未修改的选题（防止重复审查）
            valid_topics = []
            for topic in topics:
                topic_data = topic.data if hasattr(topic, 'data') else topic
                # 检查是否已经审查过（通过检查审改记录中是否有最近的小审记录）
                if not self._is_already_reviewed(topic_data):
                    valid_topics.append(topic_data)

            # 获取KOC人设
            koc = self._load_koc(context.get("koc_id", "KOC-001"))

            print(f"[小审] 找到 {len(topics)} 个待审选题，过滤后剩 {len(valid_topics)} 个")
            return {
                "topics": valid_topics,
                "koc": koc
            }
        except Exception as e:
            print(f"[小审] 读取选题库失败: {e}")
            return {"topics": [], "koc": {}}

    def _is_already_reviewed(self, topic: dict) -> bool:
        """检查选题是否已经被审查过但小改尚未修改。

        通过检查审改轮次和状态来判断：
        - 审改轮次 > 0 且 状态="审改中"：已审查，等待小改修改
        - 审改轮次 = 0 或 状态="生产中"：未审查或需要首次审查
        """
        status = topic.get("状态", "")
        review_round = topic.get("审改轮次", 0)

        # 如果状态是"审改中"且已经有审改轮次，说明已经审查过，等待小改修改
        if status == "审改中" and review_round and int(review_round) > 0:
            print(f"[小审] 选题 {topic.get('业务ID', '')} 已审查（第{review_round}轮），等待小改修改...")
            return True

        return False

    def _load_koc(self, koc_id: str) -> dict:
        """加载KOC人设。"""
        try:
            record = self.storage.get_by_id("KOC人设", koc_id)
            return record.data if record else {}
        except Exception as e:
            print(f"[小审] 加载KOC人设失败: {e}")
            return {}

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """小审不需要调用外部工具，直接返回空结果。"""
        return {}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM审查内容。

        对每个选题，对照KOC人设进行审查：
        - 事实核查
        - 风险词扫描
        - 人设一致性审查
        - 平台合规性检查
        """
        topics = upstream_data.get("topics", [])
        koc = upstream_data.get("koc", {})

        review_results = []
        for topic in topics:
            # 获取帖子内容和视频脚本（从Bitable文档字段）
            post_content = topic.get("帖子内容", "")
            script_content = topic.get("视频脚本内容", "")

            if not post_content and not script_content:
                print(f"[小审] 选题 {topic.get('业务ID', '')} 无内容可审查")
                continue

            # 解析JSON内容
            try:
                posts = json.loads(post_content) if post_content else {}
                scripts = json.loads(script_content) if script_content else {}
            except json.JSONDecodeError:
                posts = {"原始内容": post_content}
                scripts = {"原始内容": script_content}

            # 构建审查提示词
            prompt = self._build_review_prompt(topic, posts, scripts, koc)

            try:
                response = self.llm.invoke(prompt)
                review_result = self._parse_llm_response(response)

                # 获取当前审改轮次（从topic的审改轮次字段或context传入）
                current_round = topic.get("审改轮次", 0)
                if topic.get("状态") == "生产中":
                    # 首次审查
                    current_round = 1
                else:
                    # 后续审查，递增轮次
                    current_round = int(current_round) + 1 if current_round else 1

                # 强制限制最大轮次为3
                if current_round > 3:
                    current_round = 3
                    # 如果超过3轮，强制通过
                    review_result["审查结论"] = "通过"
                    review_result["严重度"] = "低"
                    review_result["发现的问题"] = []
                    print(f"[小审] 警告：选题 {topic.get('业务ID', '')} 已达到最大审改轮次，强制通过")

                review_results.append({
                    "topic_id": topic.get("id", ""),
                    "topic_title": topic.get("选题标题", ""),
                    "current_round": current_round,
                    "review_result": review_result,
                    "posts": posts,
                    "scripts": scripts,
                })
            except Exception as e:
                print(f"[小审] LLM审查失败: {e}")

        return {"review_results": review_results, "count": len(review_results)}

    def _build_review_prompt(self, topic: dict, posts: dict, scripts: dict, koc: dict) -> str:
        """构建审查提示词。"""
        # 提取KOC审查相关字段
        koc_name = koc.get("账号名", "学AI的刘同学")
        koc_forbidden = koc.get("禁区话题", "")
        koc_avoid = koc.get("不想成为的样子", "")
        koc_aesthetic = koc.get("自我审美准则", "")

        # 格式化帖子内容
        post_text = json.dumps(posts, ensure_ascii=False, indent=2) if posts else "无"
        script_text = json.dumps(scripts, ensure_ascii=False, indent=2) if scripts else "无"

        return f"""你是【小审 Reviewer】，为KOC【{koc_name}】审查内容。

KOC禁区话题：
{koc_forbidden}

KOC不想成为的样子：
{koc_avoid}

KOC自我审美准则：
{koc_aesthetic}

请审查以下内容：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}

帖子内容：
{post_text}

视频脚本：
{script_text}

请返回JSON格式：
{{
  "审查结论": "通过" | "需修改",
  "严重度": "低" | "中" | "高",
  "发现的问题": [
    {{"位置": "公众号第3段", "问题": "事实核查...", "建议": "改为..."}},
    {{"位置": "小红书标题", "问题": "调性偏差...", "建议": "改为..."}}
  ],
  "审查指标": {{
    "事实核查": "通过/1处问题",
    "风险词扫描": "通过/X处风险词",
    "人设一致性": "通过/X处偏离",
    "平台合规性": "通过/X处风险"
  }}
}}

审查标准：
1. 事实核查：技术概念、数据、引用是否准确
2. 风险词扫描：是否包含政治敏感、引战、焦虑制造等禁区话题
3. 人设一致性：是否符合KOC语气（玩梗活泼+专业硬核，不制造焦虑）
4. 平台合规性：是否符合各平台社区规范

注意：
- 如果发现问题，结论必须是"需修改"
- 如果无问题，结论必须是"通过"
- 问题列表要具体，指出位置和具体修改建议
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
            print(f"[小审] 解析LLM响应失败: {e}")
            return {
                "审查结论": "需修改",
                "严重度": "中",
                "发现的问题": [{"位置": "解析失败", "问题": "无法解析LLM响应", "建议": "请人工检查"}],
                "审查指标": {}
            }

    def _write_storage(self, context: dict, result: dict):
        """更新选题库。

        将审改记录写入Bitable"审改记录"字段（累积追加），
        并根据审查结论更新状态：
        - 需修改 → 状态="审改中"，审改轮次+1
        - 通过 → 状态="待发布"
        """
        review_results = result.get("review_results", [])

        for review in review_results:
            topic_id = review.get("topic_id", "")
            topic_title = review.get("topic_title", "")
            review_data = review.get("review_result", {})
            current_round = review.get("current_round", 1)

            # 确定新状态
            conclusion = review_data.get("审查结论", "需修改")
            if conclusion == "通过":
                new_status = "待发布"
            else:
                new_status = "审改中"

            try:
                # 生成新的审改记录条目
                review_entry = self._format_review_entry(review_data, current_round)

                # 读取现有的审改记录（如果有）
                try:
                    existing_record = self.storage.get_by_id("选题库", topic_id)
                    existing_reviews = existing_record.data.get("审改记录", "") if existing_record else ""
                except:
                    existing_reviews = ""

                # 追加新的审改记录
                updated_reviews = existing_reviews + "\n\n" + review_entry if existing_reviews else review_entry

                # 更新选题库字段
                update_data = {
                    "审改记录": updated_reviews,
                    "审改轮次": current_round,
                    "状态": new_status,
                }

                # 如果通过，记录审查通过时间
                if conclusion == "通过":
                    update_data["审查通过时间"] = int(datetime.now().timestamp() * 1000)

                self.storage.update("选题库", topic_id, update_data)
                print(f"[小审] 审查完成：{topic_title[:30]}... 结论：{conclusion}，轮次：{current_round}")
            except Exception as e:
                print(f"[小审] 更新选题库失败: {e}")

    def _format_review_entry(self, review_data: dict, round_num: int) -> str:
        """格式化审改记录条目（Markdown格式）。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conclusion = review_data.get("审查结论", "需修改")
        severity = review_data.get("严重度", "中")
        issues = review_data.get("发现的问题", [])
        metrics = review_data.get("审查指标", {})

        entry = f"""## 第 {round_num} 轮审查 ({now})

**审查结论**: {conclusion}
**严重度**: {severity}

### 发现的问题
"""

        if issues:
            for issue in issues:
                entry += f"- **{issue.get('位置', '未知位置')}**: {issue.get('问题', '')}\n"
                entry += f"  - 建议: {issue.get('建议', '')}\n"
        else:
            entry += "- 无问题\n"

        entry += "\n### 审查指标\n"
        for metric, value in metrics.items():
            entry += f"- {metric}: {value}\n"

        entry += "\n---\n"
        return entry

    def _log_work(self, context: dict, result: dict):
        """记录工作日志。"""
        count = result.get("count", 0)
        print(f"[小审] 完成：审查 {count} 条选题")
        super()._log_work(context, result)


# 保持向后兼容的别名
Reviewer = ReviewerAgent
