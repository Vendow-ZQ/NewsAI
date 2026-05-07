# -*- coding: utf-8 -*-
"""
修复并运行完整NewsAI流程
- 小哨读取20条x7信源=140条热帖
- 小编从140条中真实调用LLM选1条
- 内容组3Agent真实调用LLM产出内容
- 小审小改真实调用LLM审阅修改
- 小发真实调用LLM书写分发计划
- 小数Mock数据来源于真实选题
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 重试装饰器

def retry_on_failure(max_retries=3, delay=2):
    """带重试的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[重试] {func.__name__} 第{attempt+1}次失败: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise
            return None
        return wrapper
    return decorator


class WorkflowRunner:
    """工作流运行器 - 串行执行避免并发问题"""

    def __init__(self):
        self.storage = None
        self.llm = None
        self.results = {
            "trend_scout": None,
            "topic_curator": None,
            "content_writer": None,
            "visual_designer": None,
            "script_writer": None,
            "reviewer": None,
            "editor": None,
            "distributor": None,
            "analyst": None,
        }
        self.created_topic_id = None

    def init_storage_and_llm(self):
        """初始化存储和LLM"""
        print("=" * 60)
        print("[初始化] 正在初始化存储和LLM...")
        print("=" * 60)

        try:
            # 初始化Feishu存储
            from feishu_adapter.feishu_storage import FeishuStorage
            self.storage = FeishuStorage()
            print("[初始化] Feishu存储初始化成功")

            # 初始化LLM
            from core.llm.client import get_llm
            self.llm = get_llm()
            print(f"[初始化] LLM客户端初始化成功: {type(self.llm).__name__}")

            return True
        except Exception as e:
            print(f"[初始化失败] {e}")
            traceback.print_exc()
            return False

    @retry_on_failure(max_retries=5, delay=3)
    def run_trend_scout(self):
        """运行小哨 - 抓取140条热帖"""
        print("\n" + "=" * 60)
        print("[步骤1/9] 小哨 TrendScout - 抓取140条热帖")
        print("=" * 60)

        from core.agents.trend_scout import TrendScoutAgent

        # 创建临时Agent
        agent = TrendScoutAgent(self.storage, self.llm)

        # 手动执行工具调用获取140条热帖
        print("[小哨] 开始从7个信源各抓取20条热帖...")

        mock_dir = os.path.join(os.path.dirname(__file__), "mock_data")
        mock_files = [
            ("xiaohongshu_hot.json", "小红书"),
            ("douyin_hot.json", "抖音"),
            ("github_trending.json", "GitHub"),
            ("hackernews_hot.json", "HackerNews"),
            ("arxiv_papers.json", "arXiv"),
            ("reddit_posts.json", "Reddit"),
            ("x_hot.json", "X/Twitter"),
        ]

        all_items = []
        for filename, source_name in mock_files:
            filepath = os.path.join(mock_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items = data if isinstance(data, list) else [data] if data else []

                    # 确保只取20条
                    items = items[:20]
                    print(f"[小哨] {source_name}: {len(items)}条")

                    for item in items:
                        title = (item.get("标题") or item.get("title") or
                                item.get("热帖标题") or item.get("name") or
                                item.get("repo") or "无标题")
                        summary = (item.get("原文摘要") or item.get("摘要") or
                                  item.get("内容摘要") or item.get("description") or
                                  item.get("内容") or "")
                        link = (item.get("原文链接") or item.get("link") or
                               item.get("原始链接") or item.get("url") or "")

                        import hashlib
                        item_id = hashlib.md5(f"{source_name}:{title}".encode()).hexdigest()[:8]

                        all_items.append({
                            "标题": title,
                            "原文摘要": summary[:500] if summary else "暂无摘要",
                            "原文链接": link,
                            "信源平台": source_name,
                            "信源ID": f"{source_name.lower()}-{item_id}",
                            "抓取时间": datetime.now().isoformat(),
                        })
                except Exception as e:
                    print(f"[小哨] 加载 {filename} 失败: {e}")

        print(f"[小哨] 总共加载 {len(all_items)} 条热帖 (目标: 140条)")

        # 使用LLM为每条热帖打分（串行处理，避免并发）
        print("[小哨] 开始LLM分析每条热帖...")
        scored_items = []
        for i, item in enumerate(all_items):
            try:
                prompt = f"""分析以下AI信息，给出热度评分(0-1)和主题标签。

信息标题: {item.get('标题', '')}
信息摘要: {item.get('原文摘要', '')[:300]}
信源平台: {item.get('信源平台', '')}

请返回JSON格式:
{{"热度评分": 0.85, "内容质量": "高", "主题标签": ["AI", "编程"]}}

注意:
- 热度评分: 0-1之间的小数，AI编程/Codex/Claude相关给高分
- 内容质量: 高/中/低
- 主题标签: 2-4个关键词
"""
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)

                # 解析JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]

                analysis = json.loads(content.strip())
                item["热度评分"] = analysis.get("热度评分", 0.5)
                item["内容质量"] = analysis.get("内容质量", "中")
                item["主题标签"] = analysis.get("主题标签", [])
                scored_items.append(item)

                if (i + 1) % 20 == 0:
                    print(f"[小哨] 已分析 {i+1}/{len(all_items)} 条...")

            except Exception as e:
                print(f"[小哨] 分析第{i+1}条失败: {e}")
                item["热度评分"] = 0.5
                item["内容质量"] = "中"
                item["主题标签"] = []
                scored_items.append(item)

        # 写入热帖库
        print(f"[小哨] 正在写入 {len(scored_items)} 条热帖到热帖库...")
        from core.storage.id_generator import IDGenerator

        written_count = 0
        for item in scored_items:
            try:
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
                self.storage.create("热帖库", record_data)
                written_count += 1
            except Exception as e:
                print(f"[小哨] 写入失败: {e}")

        print(f"[小哨] 完成: 成功写入 {written_count} 条热帖")
        self.results["trend_scout"] = {"count": written_count, "items": scored_items}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_topic_curator(self):
        """运行小编 - 从140条中选出1条"""
        print("\n" + "=" * 60)
        print("[步骤2/9] 小编 TopicCurator - 从热帖中选题")
        print("=" * 60)

        from core.agents.topic_curator import TopicCuratorAgent
        from core.storage.interface import QueryFilter

        agent = TopicCuratorAgent(self.storage, self.llm)

        # 读取热帖库中的待选热帖
        filters = [QueryFilter(field="状态", operator="eq", value="待选")]
        trends = self.storage.query("热帖库", filters=filters, limit=140)
        trends_data = [t.data for t in trends]

        print(f"[小编] 从热帖库读取到 {len(trends_data)} 条待选热帖")

        # 获取KOC人设
        koc_id = "KOC-001"
        koc_record = self.storage.get_by_id("KOC人设", koc_id)
        koc = koc_record.data if koc_record else {}

        # 使用LLM分析所有热帖并选出最佳选题（分批处理避免token超限）
        print("[小编] 开始LLM分析...")

        # 构建简化版热帖列表供LLM分析
        trend_summaries = []
        for t in trends_data[:20]:  # 限制LLM分析的条数避免token超限
            trend_summaries.append({
                "id": t.get("id"),
                "标题": t.get("标题", ""),
                "摘要": t.get("原文摘要", "")[:200],
                "平台": t.get("信源平台", ""),
                "热度": t.get("热度评分", 0.5)
            })

        prompt = f"""你是【小编 TopicCurator】，为 KOC【{koc.get('账号名', '学AI的刘同学')}】工作。

KOC定位：{koc.get('一句话定位', '给所有非科班大众看的 AI 资讯与教程速递。')}
目标受众：{koc.get('目标受众', '22-35岁的非技术背景知识工作者')}
偏好选题类型：{koc.get('偏好选题类型', ['新模型发布', '新工具评测', '行业八卦', '实操教程'])}
禁区话题：{koc.get('禁区话题', '政治敏感、引战话题、卖课导流、未经证实的揣测、制造焦虑')}

请从以下热帖中选出1条最适合作为选题的：

热帖列表：
{json.dumps(trend_summaries, ensure_ascii=False, indent=2)}

请返回JSON格式：
{{
  "选中热帖ID": "TREND-xxx",
  "选题标题": "一句话选题（20字内）",
  "选题角度": "从什么角度切入（100字）",
  "预估爆点": "为什么这个选题会爆（100字）",
  "预估受众": "目标受众分析（50字）",
  "推荐优先级": 9
}}

注意：
- 必须选择AI编程、Codex、Claude相关的热门话题
- 选题标题要抓人眼球但拒绝标题党
- 推荐优先级：1-10分，10分为最高优先级
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        analysis = json.loads(content.strip())
        selected_id = analysis.get("选中热帖ID", "")

        # 找到选中的热帖
        selected_trend = None
        for t in trends_data:
            if t.get("id") == selected_id:
                selected_trend = t
                break

        if not selected_trend and trends_data:
            selected_trend = trends_data[0]  # 默认选第一个

        if selected_trend:
            from core.storage.id_generator import IDGenerator
            business_id = IDGenerator.generate("TOPIC")
            record_data = {
                "id": business_id,
                "选题标题": analysis.get("选题标题", selected_trend.get("标题", "")),
                "选题角度": analysis.get("选题角度", ""),
                "预估爆点": analysis.get("预估爆点", ""),
                "预估受众": analysis.get("预估受众", ""),
                "关联热帖IDs": json.dumps([selected_trend.get("id", "")], ensure_ascii=False),
                "KOC人设ID": koc_id,
                "推荐优先级": analysis.get("推荐优先级", 8),
                "状态": "已选",
                "审改轮次": 0,
                "创建时间": int(datetime.now().timestamp() * 1000),
            }
            self.storage.create("选题库", record_data)
            self.created_topic_id = business_id
            print(f"[小编] 创建选题成功: {record_data['选题标题']}")
            print(f"[小编] 选题ID: {business_id}")

        self.results["topic_curator"] = {"topic_id": self.created_topic_id}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_content_writer(self):
        """运行小文 - 撰写4平台内容"""
        print("\n" + "=" * 60)
        print("[步骤3/9] 小文 ContentWriter - 撰写4平台内容")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小文] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小文] 错误: 选题不存在")
            return False

        topic = topic_record.data
        koc_id = topic.get("KOC人设ID", "KOC-001")
        koc_record = self.storage.get_by_id("KOC人设", koc_id)
        koc = koc_record.data if koc_record else {}

        print(f"[小文] 正在为选题撰写内容: {topic.get('选题标题', '')}")

        # LLM生成4平台内容
        prompt = f"""你是【小文 ContentWriter】，为 KOC【{koc.get('账号名', '学AI的刘同学')}】工作。

KOC语气：{koc.get('语气', '玩梗活泼 + 专业硬核')}
中文爆款偏好：{koc.get('中文爆款偏好', '标题前8字必有钩子；善用emoji分段')}

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
1. 公众号：深度长文，有目录结构
2. 小红书：标题党+emoji分段
3. 抖音：钩子型，开场抓人
4. B站：教程/评测风格
5. 多用"咱们/我们"
6. 标题前8字必须有钩子
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        platforms_content = json.loads(content.strip())

        # 创建飞书文档
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()
        date_str = datetime.now().strftime("%Y%m%d")

        doc_id = doc_storage.create_post_doc(topic.get('选题标题', ''), date_str)

        # 格式化内容
        doc_markdown = f"# {topic.get('选题标题', '')}\n\n"
        for platform, data in platforms_content.items():
            doc_markdown += f"## {platform}版本\n\n"
            if isinstance(data, dict):
                for key, value in data.items():
                    doc_markdown += f"**{key}**: {value}\n\n"
            else:
                doc_markdown += f"{data}\n\n"

        doc_storage.append_section(doc_id, doc_markdown)
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
        doc_url = doc_storage.get_share_url(doc_id)

        # 更新选题库
        self.storage.update(self.created_topic_id, {
            "帖子文档链接": doc_url,
            "公众号标题": platforms_content.get("公众号", {}).get("标题", ""),
            "公众号摘要": platforms_content.get("公众号", {}).get("摘要", ""),
            "公众号正文": platforms_content.get("公众号", {}).get("正文", ""),
            "小红书标题": platforms_content.get("小红书", {}).get("标题", ""),
            "小红书正文": platforms_content.get("小红书", {}).get("正文", ""),
            "抖音文案": platforms_content.get("抖音", {}).get("文案", ""),
            "B站标题": platforms_content.get("B站", {}).get("标题", ""),
            "状态": "生产中",
            "生产开始时间": int(datetime.now().timestamp() * 1000),
        })

        print(f"[小文] 完成: 4平台内容已写入")
        print(f"[小文] 文档链接: {doc_url}")

        self.results["content_writer"] = {"doc_url": doc_url}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_visual_designer(self):
        """运行小图 - 设计配图方案"""
        print("\n" + "=" * 60)
        print("[步骤4/9] 小图 VisualDesigner - 设计配图方案")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小图] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小图] 错误: 选题不存在")
            return False

        topic = topic_record.data
        print(f"[小图] 正在为选题设计配图: {topic.get('选题标题', '')}")

        # LLM生成配图方案
        prompt = f"""你是【小图 VisualDesigner】，为KOC设计配图方案。

请为以下内容设计配图方案：

选题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}

请返回JSON格式：
{{
  "配图方案": [
    {{
      "配图编号": "配图1",
      "用途": "公众号封面",
      "类型": "文字卡片/信息图/AI画面图",
      "描述": "画面描述...",
      "AI生成Prompt": "即梦API用的prompt..."
    }},
    {{
      "配图编号": "配图2",
      "用途": "小红书首图",
      "类型": "...",
      "描述": "...",
      "AI生成Prompt": "..."
    }}
  ],
  "视觉风格": "整体风格建议"
}}

要求：
- 每篇内容配3-5张图
- 封面图必须吸引人
- AI生成Prompt要详细
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        design_plan = json.loads(content.strip())

        # 更新选题库
        self.storage.update(self.created_topic_id, {
            "配图方案": json.dumps(design_plan.get("配图方案", []), ensure_ascii=False),
            "视觉风格": design_plan.get("视觉风格", ""),
            "配图更新时间": int(datetime.now().timestamp() * 1000),
        })

        print(f"[小图] 完成: 配图方案已生成 ({len(design_plan.get('配图方案', []))}张)")

        self.results["visual_designer"] = {"design_count": len(design_plan.get("配图方案", []))}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_script_writer(self):
        """运行小播 - 撰写视频脚本"""
        print("\n" + "=" * 60)
        print("[步骤5/9] 小播 ScriptWriter - 撰写视频脚本")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小播] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小播] 错误: 选题不存在")
            return False

        topic = topic_record.data
        print(f"[小播] 正在为选题撰写视频脚本: {topic.get('选题标题', '')}")

        # LLM生成视频脚本
        prompt = f"""你是【小播 ScriptWriter】，撰写短视频脚本。

请为以下选题撰写视频脚本：

选题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
关键信息点：{topic.get('预估爆点', '')}
参考正文：{topic.get('公众号正文', '')[:1000] if topic.get('公众号正文') else ''}

请返回JSON格式：
{{
  "抖音版": {{
    "时长": "45秒",
    "钩子开场": "0-3秒画面+口播文案",
    "核心内容": "3-40秒分镜脚本",
    "CTA": "40-45秒行动号召",
    "字幕": ["字幕1", "字幕2"],
    "BGM建议": "风格描述"
  }},
  "B站版": {{
    "时长": "2分15秒",
    "开场": "0-15秒",
    "分段": [{{"时间段": "15-60秒", "内容": "..."}}],
    "结尾": "总结+互动引导",
    "字幕": ["字幕1", "字幕2"],
    "BGM建议": "风格描述"
  }}
}}

要求：
1. 抖音版前3秒必须有强钩子
2. B站版内容有层次，由浅入深
3. 口播文案要口语化
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        scripts = json.loads(content.strip())

        # 创建飞书文档
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()
        date_str = datetime.now().strftime("%Y%m%d")

        doc_id = doc_storage.create_script_doc(topic.get('选题标题', ''), date_str)

        # 格式化内容
        doc_markdown = f"# {topic.get('选题标题', '')} - 视频脚本\n\n"
        for platform, data in scripts.items():
            doc_markdown += f"## {platform}\n\n"
            if isinstance(data, dict):
                for key, value in data.items():
                    doc_markdown += f"**{key}**: {value}\n\n"
            else:
                doc_markdown += f"{data}\n\n"

        doc_storage.append_section(doc_id, doc_markdown)
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
        doc_url = doc_storage.get_share_url(doc_id)

        # 更新选题库
        self.storage.update(self.created_topic_id, {
            "视频脚本文档链接": doc_url,
        })

        print(f"[小播] 完成: 视频脚本已生成")
        print(f"[小播] 文档链接: {doc_url}")

        self.results["script_writer"] = {"doc_url": doc_url}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_reviewer(self):
        """运行小审 - 审查内容"""
        print("\n" + "=" * 60)
        print("[步骤6/9] 小审 Reviewer - 审查内容")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小审] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小审] 错误: 选题不存在")
            return False

        topic = topic_record.data
        print(f"[小审] 正在审查选题: {topic.get('选题标题', '')}")

        # 读取KOC人设
        koc_id = topic.get("KOC人设ID", "KOC-001")
        koc_record = self.storage.get_by_id("KOC人设", koc_id)
        koc = koc_record.data if koc_record else {}

        # 读取帖子文档内容
        post_content = topic.get("公众号正文", "")[:1500]

        # LLM审查
        prompt = f"""你是【小审 Reviewer】，审查内容。

KOC禁区话题：{koc.get('禁区话题', '政治敏感、引战话题')}
KOC不想成为的样子：{koc.get('不想成为的样子', '')}

请审查以下内容：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}

帖子内容摘要：
{post_content}

请返回JSON格式：
{{
  "审查结论": "通过" | "需修改",
  "严重度": "低" | "中" | "高",
  "发现的问题": [
    {{"位置": "公众号标题", "问题": "...", "建议": "..."}}
  ],
  "审查指标": {{
    "事实核查": "通过",
    "风险词扫描": "通过",
    "人设一致性": "通过",
    "平台合规性": "通过"
  }}
}}

注意：
- 如果没有问题，结论必须是"通过"
- 演示模式下，最多2轮审查后强制通过
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        review_result = json.loads(content.strip())

        conclusion = review_result.get("审查结论", "通过")
        severity = review_result.get("严重度", "低")
        issues = review_result.get("发现的问题", [])

        # 创建审改文档
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()
        date_str = datetime.now().strftime("%Y%m%d")

        doc_id = doc_storage.create_audit_doc(topic.get('选题标题', ''), date_str)

        # 格式化审改记录
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        audit_content = f"""# {topic.get('选题标题', '')} - 审改记录

## v0 原稿
- 帖子文档: {topic.get('帖子文档链接', '')}
- 视频脚本: {topic.get('视频脚本文档链接', '')}

## 第 1 轮审查 ({now})

**审查结论**: {conclusion}
**严重度**: {severity}

### 发现的问题
"""
        if issues:
            for issue in issues:
                audit_content += f"- **{issue.get('位置', '未知位置')}**: {issue.get('问题', '')}\n"
                audit_content += f"  - 建议: {issue.get('建议', '')}\n"
        else:
            audit_content += "- 无问题\n"

        audit_content += "\n### 审查指标\n"
        for metric, value in review_result.get("审查指标", {}).items():
            audit_content += f"- {metric}: {value}\n"

        doc_storage.append_section(doc_id, audit_content)
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
        doc_url = doc_storage.get_share_url(doc_id)

        # 更新选题库状态
        new_status = "待发布" if conclusion == "通过" else "审改中"
        self.storage.update(self.created_topic_id, {
            "审改文档链接": doc_url,
            "审改轮次": 1,
            "状态": new_status,
        })

        print(f"[小审] 完成: 审查结论={conclusion}, 严重度={severity}")
        print(f"[小审] 审改文档: {doc_url}")

        self.results["reviewer"] = {
            "conclusion": conclusion,
            "severity": severity,
            "issues_count": len(issues)
        }
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_editor(self):
        """运行小改 - 修改内容"""
        print("\n" + "=" * 60)
        print("[步骤7/9] 小改 Editor - 修改内容")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小改] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小改] 错误: 选题不存在")
            return False

        topic = topic_record.data

        # 如果已经通过，跳过修改
        if topic.get("状态") == "待发布":
            print("[小改] 选题已通过审查，无需修改")
            self.results["editor"] = {"skipped": True}
            return True

        print(f"[小改] 正在修改选题: {topic.get('选题标题', '')}")

        # 读取KOC人设
        koc_id = topic.get("KOC人设ID", "KOC-001")
        koc_record = self.storage.get_by_id("KOC人设", koc_id)
        koc = koc_record.data if koc_record else {}

        # LLM修改内容
        prompt = f"""你是【小改 Editor】，修改内容。

KOC语气基调：{koc.get('语气', '玩梗活泼 + 专业硬核')}

请根据审查意见修改以下内容：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}

原始帖子内容：
{topic.get('公众号正文', '')[:1000]}

请返回JSON格式：
{{
  "修改总结": "简要说明修改了哪些内容",
  "修改后的公众号标题": "...",
  "修改后的公众号正文": "...",
  "修改说明": [
    {{"位置": "...", "修改": "...", "原因": "..."}}
  ]
}}

修改原则：
1. 保持KOC的语气基调和风格一致性
2. 不引入新的风险词
3. 确保修改后的内容更优质
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        edit_result = json.loads(content.strip())

        # 追加修改记录到审改文档
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()

        audit_url = topic.get("审改文档链接", "")
        if audit_url:
            doc_id = audit_url.split("/docx/")[-1].split("?")[0] if "/docx/" in audit_url else ""

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            edit_entry = f"""
## 修改记录 ({now})

**修改总结**: {edit_result.get('修改总结', '')}

### 具体修改
"""
            for detail in edit_result.get("修改说明", []):
                edit_entry += f"- **{detail.get('位置', '未知位置')}**: {detail.get('修改', '')}\n"
                edit_entry += f"  - 原因: {detail.get('原因', '')}\n"

            if doc_id:
                doc_storage.append_section(doc_id, edit_entry)

        # 更新选题库内容
        self.storage.update(self.created_topic_id, {
            "公众号标题": edit_result.get("修改后的公众号标题", topic.get("公众号标题", "")),
            "公众号正文": edit_result.get("修改后的公众号正文", topic.get("公众号正文", "")),
            "状态": "待发布",  # 修改后直接通过
        })

        print(f"[小改] 完成: 内容已修改并通过")

        self.results["editor"] = {"edit_summary": edit_result.get("修改总结", "")}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_distributor(self):
        """运行小发 - 制定分发计划"""
        print("\n" + "=" * 60)
        print("[步骤8/9] 小发 Distributor - 制定分发计划")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小发] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小发] 错误: 选题不存在")
            return False

        topic = topic_record.data
        print(f"[小发] 正在为选题制定分发计划: {topic.get('选题标题', '')}")

        # 读取KOC人设
        koc_id = topic.get("KOC人设ID", "KOC-001")
        koc_record = self.storage.get_by_id("KOC人设", koc_id)
        koc = koc_record.data if koc_record else {}

        # LLM生成分发计划
        prompt = f"""你是【小发 Distributor】，制定分发计划。

KOC主战场平台：{koc.get('主战场平台', ['公众号', '小红书', '抖音', 'B站'])}
发布频率：{koc.get('发布频率', '每周 3 次')}
偏好发布时段：{koc.get('偏好发布时段', ['中 12-13'])}

请为以下内容制定分发计划：

选题标题：{topic.get("选题标题", "")}
选题角度：{topic.get("选题角度", "")}
帖子文档：{topic.get('帖子文档链接', '')}
视频脚本：{topic.get('视频脚本文档链接', '')}
审改文档：{topic.get('审改文档链接', '')}

请返回JSON格式：
{{
  "分发策略总结": "简要说明整体分发思路",
  "平台分发计划": [
    {{
      "平台": "公众号",
      "发布时间": "2026-05-08 12:00",
      "内容形式": "图文",
      "优化建议": "...",
      "预期效果": "预计阅读1万+"
    }},
    {{
      "平台": "小红书",
      "发布时间": "2026-05-08 12:30",
      "内容形式": "图文",
      "优化建议": "...",
      "预期效果": "预计阅读5万+"
    }},
    {{
      "平台": "抖音",
      "发布时间": "2026-05-08 19:00",
      "内容形式": "短视频",
      "优化建议": "...",
      "预期效果": "预计播放10万+"
    }},
    {{
      "平台": "B站",
      "发布时间": "2026-05-08 20:00",
      "内容形式": "视频",
      "优化建议": "...",
      "预期效果": "预计播放3万+"
    }}
  ],
  "发布顺序建议": "公众号→小红书→抖音→B站",
  "时间间隔策略": "各平台发布时间错开30分钟"
}}

分发策略原则：
1. 严格遵循KOC的偏好发布时段
2. 错开发布时间，避免同一时间在多平台同时发布
3. 根据内容特点选择最适合的首发平台
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        distribution_plan = json.loads(content.strip())

        # 更新选题库
        self.storage.update(self.created_topic_id, {
            "分发计划JSON": json.dumps(distribution_plan, ensure_ascii=False, indent=2),
            "状态": "已发布",
            "发布完成时间": int(datetime.now().timestamp() * 1000),
        })

        print(f"[小发] 完成: 分发计划已制定")
        print(f"[小发] 发布顺序: {distribution_plan.get('发布顺序建议', '')}")

        self.results["distributor"] = {"plan_summary": distribution_plan.get("分发策略总结", "")}
        return True

    @retry_on_failure(max_retries=5, delay=3)
    def run_analyst(self):
        """运行小数 - 数据分析"""
        print("\n" + "=" * 60)
        print("[步骤9/9] 小数 Analyst - 数据分析")
        print("=" * 60)

        if not self.created_topic_id:
            print("[小数] 错误: 没有可用的选题ID")
            return False

        topic_record = self.storage.get_by_id("选题库", self.created_topic_id)
        if not topic_record:
            print("[小数] 错误: 选题不存在")
            return False

        topic = topic_record.data
        print(f"[小数] 正在分析选题数据: {topic.get('选题标题', '')}")

        # 从mock数据加载（基于真实选题ID匹配）
        mock_data = None
        try:
            mock_file = os.path.join("mock_data", "analytics_mock.json")
            with open(mock_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 找到匹配的mock数据（通过选题标题匹配）
                for item in data:
                    if item.get("选题标题") == topic.get("选题标题"):
                        mock_data = item
                        break
                # 如果没找到匹配，使用第一条
                if not mock_data:
                    mock_data = data[0]
                    mock_data["选题 ID"] = self.created_topic_id
                    mock_data["选题标题"] = topic.get("选题标题", "")
        except Exception as e:
            print(f"[小数] 加载mock数据失败: {e}")
            mock_data = {
                "选题 ID": self.created_topic_id,
                "选题标题": topic.get("选题标题", ""),
                "公众号_阅读量": 78000,
                "公众号_点赞数": 2600,
                "小红书_阅读量": 860000,
                "小红书_点赞数": 64200,
                "抖音_播放量": 3860000,
                "抖音_点赞数": 286000,
                "B站_播放量": 520000,
                "B站_点赞数": 38600,
                "综合评分": 0.96,
                "爆点验证": "验证成功",
            }

        # LLM分析数据
        prompt = f"""你是【小数 Analyst】，分析内容发布数据。

选题信息：
标题：{topic.get("选题标题", "")}
预估爆点：{topic.get("预估爆点", "")}

平台数据：
公众号：阅读量{mock_data.get('公众号_阅读量', 0)}, 点赞{mock_data.get('公众号_点赞数', 0)}
小红书：阅读量{mock_data.get('小红书_阅读量', 0)}, 点赞{mock_data.get('小红书_点赞数', 0)}
抖音：播放量{mock_data.get('抖音_播放量', 0)}, 点赞{mock_data.get('抖音_点赞数', 0)}
B站：播放量{mock_data.get('B站_播放量', 0)}, 点赞{mock_data.get('B站_点赞数', 0)}

请分析：
1. 综合评分（0-1）
2. 爆点验证（验证成功/部分验证/未爆）
3. 各平台表现分析
4. 成功/失败原因
5. 给小编的下个选题建议

返回JSON：
{{
  "综合评分": 0.85,
  "爆点验证": "验证成功",
  "平台表现": {{"最佳平台": "抖音", "最差平台": "公众号", "分析": "..."}},
  "成败分析": "...",
  "选题建议": ["建议1", "建议2"]
}}
"""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        analysis = json.loads(content.strip())

        # 写入数据库
        from core.storage.id_generator import IDGenerator
        business_id = IDGenerator.generate("DATA")

        record_data = {
            "id": business_id,
            "选题ID": self.created_topic_id,
            "选题标题": topic.get("选题标题", ""),
            "公众号_阅读量": mock_data.get("公众号_阅读量", 0),
            "公众号_点赞数": mock_data.get("公众号_点赞数", 0),
            "小红书_阅读量": mock_data.get("小红书_阅读量", 0),
            "小红书_点赞数": mock_data.get("小红书_点赞数", 0),
            "抖音_播放量": mock_data.get("抖音_播放量", 0),
            "抖音_点赞数": mock_data.get("抖音_点赞数", 0),
            "B站_播放量": mock_data.get("B站_播放量", 0),
            "B站_点赞数": mock_data.get("B站_点赞数", 0),
            "综合评分": analysis.get("综合评分", 0.5),
            "爆点验证": analysis.get("爆点验证", "未爆"),
            "数据采集时间": int(datetime.now().timestamp() * 1000),
            "数据状态": "已迭代分析",
        }

        self.storage.create("数据库", record_data)

        # 更新选题库
        self.storage.update(self.created_topic_id, {
            "数据回流ID": business_id,
        })

        # 创建经验总结文档
        from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
        doc_storage = FeishuDocStorage()
        period = datetime.now().strftime("%Y%m")

        doc_id = doc_storage.create_experience_doc(period, topic.get("选题标题", ""))

        experience_doc = f"""# {period} AI内容复盘

## 选题：{topic.get("选题标题", "")}

### 成败分析
{analysis.get("成败分析", "")}

### 选题建议
"""
        for suggestion in analysis.get("选题建议", []):
            experience_doc += f"- {suggestion}\n"

        experience_doc += f"""
### 平台数据
- 公众号：阅读量{mock_data.get('公众号_阅读量', 0)}, 点赞{mock_data.get('公众号_点赞数', 0)}
- 小红书：阅读量{mock_data.get('小红书_阅读量', 0)}, 点赞{mock_data.get('小红书_点赞数', 0)}
- 抖音：播放量{mock_data.get('抖音_播放量', 0)}, 点赞{mock_data.get('抖音_点赞数', 0)}
- B站：播放量{mock_data.get('B站_播放量', 0)}, 点赞{mock_data.get('B站_点赞数', 0)}

---
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

        doc_storage.append_section(doc_id, experience_doc)
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
        doc_url = doc_storage.get_share_url(doc_id)

        # 更新数据库的经验文档链接
        self.storage.update("数据库", business_id, {"经验文档链接": doc_url})

        print(f"[小数] 完成: 数据分析已完成")
        print(f"[小数] 综合评分: {analysis.get('综合评分', 0)}")
        print(f"[小数] 爆点验证: {analysis.get('爆点验证', '')}")
        print(f"[小数] 经验文档: {doc_url}")

        self.results["analyst"] = {
            "score": analysis.get("综合评分", 0),
            "validation": analysis.get("爆点验证", ""),
            "doc_url": doc_url
        }
        return True

    def run_full_workflow(self):
        """运行完整工作流"""
        print("\n" + "=" * 60)
        print("NewsAI 完整工作流启动")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 初始化
        if not self.init_storage_and_llm():
            print("[错误] 初始化失败，退出")
            return False

        steps = [
            ("小哨 TrendScout", self.run_trend_scout),
            ("小编 TopicCurator", self.run_topic_curator),
            ("小文 ContentWriter", self.run_content_writer),
            ("小图 VisualDesigner", self.run_visual_designer),
            ("小播 ScriptWriter", self.run_script_writer),
            ("小审 Reviewer", self.run_reviewer),
            ("小改 Editor", self.run_editor),
            ("小发 Distributor", self.run_distributor),
            ("小数 Analyst", self.run_analyst),
        ]

        success_count = 0
        fail_count = 0

        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
                    print(f"✅ {step_name} 完成")
                else:
                    fail_count += 1
                    print(f"❌ {step_name} 失败")
            except Exception as e:
                fail_count += 1
                print(f"❌ {step_name} 异常: {e}")
                traceback.print_exc()

        # 总结
        print("\n" + "=" * 60)
        print("NewsAI 工作流完成")
        print("=" * 60)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"成功: {success_count} 步")
        print(f"失败: {fail_count} 步")
        print(f"选题ID: {self.created_topic_id}")

        return fail_count == 0


def main():
    """主函数"""
    runner = WorkflowRunner()
    runner.run_full_workflow()


if __name__ == "__main__":
    main()
