#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容生产流水线 - 运行小文、小图、小审、小改 (修复版)"""

import sys
import os

# 设置环境变量避免Unicode问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from core.storage.interface import QueryFilter
from datetime import datetime

# 导入Agent
from core.agents.content_writer import ContentWriterAgent
from core.agents.visual_designer import VisualDesignerAgent
from core.agents.reviewer import ReviewerAgent
from core.agents.editor import EditorAgent


class SimpleMockLLM:
    """简化版Mock LLM - 快速返回结果避免超时"""

    def invoke(self, prompt):
        prompt_str = str(prompt)

        if "公众号" in prompt_str or "小红书" in prompt_str or "抖音" in prompt_str or "B站" in prompt_str:
            # 返回4平台内容
            return '''{
  "公众号": {
    "标题": "AI效率革命：这款大模型让工作速度翻倍，打工人必备神器",
    "摘要": "揭秘最新AI技术突破，实测效率提升200%",
    "正文": "姐妹们/兄弟们，今天给大家安利一个超神的AI工具！\\n\\n最近我在日常工作中发现了一个大模型，用了一周后效率直接翻倍。不是夸张，是真实的效率提升。\\n\\n## 效率对比实测\\n\\n以前写一份报告需要4小时，现在只需要1.5小时。\\n\\n以前整理数据需要半天，现在30分钟搞定。\\n\\n## 核心功能解析\\n\\n这个AI有三个让我惊艳的功能：\\n\\n1. **智能理解上下文**：不像其他AI需要反复解释，它一次就能get到你的需求\\n\\n2. **多任务并行处理**：可以同时处理文档、数据、代码，不用切换工具\\n\\n3. **自适应学习**：用越久越懂你的工作习惯，推荐越精准\\n\\n## 真实使用场景\\n\\n上周五老板临时要一份竞品分析，平时这种任务我至少要做一天。结果用这个AI，2小时就交差了，还被表扬做得好。\\n\\n## 适合谁用\\n\\n- 经常写报告、做PPT的职场人\\n- 需要处理大量数据的分析师\\n- 想提升学习效率的学生党\\n- 自媒体创作者\\n\\n## 使用建议\\n\\n刚开始用的时候建议从简单任务入手，慢慢熟悉它的交互方式。不要一上来就指望它解决所有问题，给它一点学习时间。\\n\\n## 总结\\n\\nAI不是要替代我们，而是让我们从重复劳动中解放出来，去做更有创造性的事情。效率提升后，我终于有时间做一直想做的副业项目了。\\n\\n你们平时在工作中最大的效率瓶颈是什么？评论区聊聊，看看AI能不能帮到你们！",
    "配图说明": "科技感封面图+效率对比示意图+使用场景图"
  },
  "小红书": {
    "标题": "这款AI让我的效率翻倍！打工人救命神器",
    "正文": "姐妹们！发现一款超神的AI工具！🚀\\n\\n用了一周，效率直接翻倍！\\n以前4小时的报告，现在1.5小时搞定✅\\n\\n三个核心功能：\\n1️⃣ 智能理解上下文，一次get需求\\n2️⃣ 多任务并行，不用切换工具\\n3️⃣ 自适应学习，越用越懂你\\n\\n上周五2小时完成竞品分析\\n还被老板表扬了哈哈哈\\n\\n适合：\\n✔️ 经常写报告的职场人\\n✔️ 处理数据的分析师\\n✔️ 想提升效率的学生党\\n\\n#AI工具 #效率神器 #打工人必备 #职场干货 #效率提升 #AI助手",
    "标签": "#AI工具 #效率神器 #打工人必备 #职场干货 #效率提升 #AI助手"
  },
  "抖音": {
    "文案": "你们知道吗？最新的AI大模型让我的工作效率直接翻倍！\\n\\n以前我写一份报告要4个小时，现在1.5小时就搞定了。\\n\\n最绝的是上周五，老板临时要竞品分析，平时要一天的任务，我用了2小时就完成了，还被表扬了！\\n\\n这个AI有三个超牛的功能：智能理解上下文、多任务并行处理、自适应学习你的工作习惯。\\n\\n评论区告诉我，你最想用AI提升哪方面的效率？",
    "钩子": "效率翻倍的关键就在这个设置",
    "CTA": "评论区告诉我你最想用AI做什么"
  },
  "B站": {
    "标题": "【实测】最新大模型效率翻倍？打工人真实使用体验",
    "简介": "本期深度测试一款AI大模型工具，真实使用一周后效率提升200%，从写作到数据分析全面评测。",
    "正文": "大家好，欢迎来到本期视频。\\n\\n今天我要分享的是一款最近发现的AI大模型，用了一周后我的工作效率直接翻倍。\\n\\n【测试背景】\\n\\n作为打工人，我日常需要写报告、做PPT、整理数据，这些重复性工作占用了大量时间。\\n\\n【效率对比】\\n\\n我先做了一个对照实验：\\n\\n同样的报告任务\\n- 传统方式：4小时\\n- 使用AI辅助：1.5小时\\n\\n数据处理任务\\n- 以前：半天\\n- 现在：30分钟\\n\\n【核心功能】\\n\\n让我惊艳的三个功能：\\n\\n1. 智能理解上下文\\n\\n不像其他AI需要反复解释需求，这款大模型一次就能理解你的意图。\\n\\n2. 多任务并行处理\\n\\n可以同时处理文档、数据、代码，不用在不同工具之间切换。\\n\\n3. 自适应学习\\n\\n用的时间越长，它越懂你的工作习惯，推荐越精准。\\n\\n【真实案例】\\n\\n上周五老板临时要一份竞品分析，平时这种任务至少要做一天。结果用AI辅助，2小时就交差了，还被表扬做得好。\\n\\n【适合人群】\\n\\n- 经常写报告、做PPT的职场人\\n- 需要处理大量数据的分析师\\n- 想提升学习效率的学生党\\n- 自媒体创作者\\n\\n【使用建议】\\n\\n刚开始用建议从简单任务入手，慢慢熟悉交互方式。不要一开始就指望解决所有问题，给它一点学习时间。\\n\\n【总结】\\n\\nAI不是要替代我们，而是让我们从重复劳动中解放出来，去做更有创造性的事情。\\n\\n效率提升后，我终于有时间做一直想做的副业项目了。\\n\\n你们平时在工作中最大的效率瓶颈是什么？欢迎在评论区讨论，我会挑选几个典型场景测试AI的解决方案。\\n\\n如果觉得这期视频有帮助，记得一键三连支持一下！我们下期再见！"
  }
}'''

        elif "配图" in prompt_str or "即梦" in prompt_str or "视觉" in prompt_str:
            return '''{
  "配图方案": [
    {
      "配图编号": "配图1",
      "用途": "公众号封面/小红书首图",
      "类型": "文字卡片",
      "描述": "科技感背景+大标题'效率翻倍'，蓝色渐变配色",
      "技术方案": "HTML模板渲染",
      "AI生成Prompt": "",
      "对应正文位置": "封面"
    },
    {
      "配图编号": "配图2",
      "用途": "正文插图",
      "类型": "信息图",
      "描述": "效率对比柱状图，传统方式4小时 vs AI辅助1.5小时",
      "技术方案": "SVG模板",
      "AI生成Prompt": "",
      "对应正文位置": "效率对比实测部分"
    },
    {
      "配图编号": "配图3",
      "用途": "正文插图",
      "类型": "AI画面图",
      "描述": "AI大脑神经网络图，科技感蓝色光效",
      "技术方案": "即梦API",
      "AI生成Prompt": "futuristic AI brain, neural networks, blue glow, high tech, digital art, clean background",
      "对应正文位置": "核心功能解析"
    },
    {
      "配图编号": "配图4",
      "用途": "使用场景展示",
      "类型": "AI画面图",
      "描述": "职场人使用笔记本电脑工作，屏幕发出蓝光",
      "技术方案": "即梦API",
      "AI生成Prompt": "professional person working on laptop, blue screen glow, modern office, tech vibe, realistic photo style",
      "对应正文位置": "真实使用场景"
    }
  ],
  "视觉风格": "简洁科技风，蓝白配色为主，突出效率感和专业性"
}'''

        elif "审查" in prompt_str or "风险词" in prompt_str or "合规" in prompt_str:
            return '''{
  "审查结论": "通过",
  "严重度": "低",
  "发现的问题": [],
  "审查指标": {
    "事实核查": "通过",
    "风险词扫描": "通过",
    "人设一致性": "通过",
    "平台合规性": "通过"
  }
}'''

        elif "修改" in prompt_str or "审改" in prompt_str:
            return '''{
  "修改总结": "内容质量良好，无需重大修改",
  "修改后的帖子内容": {},
  "修改后的视频脚本": {},
  "修改说明": []
}'''

        else:
            return '{"result": "success"}'


def run_content_pipeline():
    """运行内容生产全流程"""
    print("=" * 60)
    print("NewsAI Content Production Pipeline")
    print("=" * 60)

    # 初始化存储和LLM
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    llm = SimpleMockLLM()  # 使用Mock避免超时

    # 找一个待生产的选题（已选状态）
    print("\n[0] Finding pending topic...")
    all_topics = storage.query("选题库", limit=100)
    pending_topics = [t for t in all_topics if t.data.get("状态") == "已选"]

    if not pending_topics:
        print("  No pending topics found. Please run TopicCurator first.")
        return

    topic = pending_topics[-1].data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "Untitled")
    print(f"  Selected: {topic_title}")
    print(f"  Topic ID: {topic_id}")

    # Step 1: 小文 - 生成内容并创建飞书文档
    print("\n[1] Running ContentWriter...")
    print("-" * 40)

    writer = ContentWriterAgent(storage, llm)
    writer_result = writer.execute({"topic_ids": [topic_id]})

    count = writer_result.get('count', 0)
    print(f"  Done: Written {count} topics 4-platform versions")

    # 获取生成的文档链接
    topic_updated = storage.get_by_id("选题库", topic_id)
    post_doc_url = topic_updated.data.get("帖子文档链接", "") if topic_updated else ""
    print(f"  Post doc link: {post_doc_url}")

    # Step 2: 小图 - 生成配图方案
    print("\n[2] Running VisualDesigner...")
    print("-" * 40)

    visual = VisualDesignerAgent(storage, llm)
    visual_result = visual.execute({"topic_id": topic_id})

    count = visual_result.get('count', 0)
    print(f"  Done: Generated visual designs for {count} topics")
    designs = visual_result.get("designs", [])
    if designs:
        design = designs[0]
        schemes = design.get('配图方案', [])
        style = design.get('视觉风格', '')
        print(f"  Visual scheme: {len(schemes)} images")
        print(f"  Visual style: {style}")

    # Step 3: 小审 - 审查内容并创建审改文档
    print("\n[3] Running Reviewer...")
    print("-" * 40)

    reviewer = ReviewerAgent(storage, llm)
    review_result = reviewer.execute({"topic_id": topic_id})

    reviews = review_result.get("review_results", [])
    if reviews:
        review = reviews[0]
        review_data = review.get("review_result", {})
        conclusion = review_data.get("审查结论", "Unknown")
        severity = review_data.get("严重度", "Unknown")
        issues = review_data.get("发现的问题", [])
        print(f"  Review conclusion: {conclusion}")
        print(f"  Severity: {severity}")
        print(f"  Issues found: {len(issues)}")

        # 获取审改文档链接
        topic_after_review = storage.get_by_id("选题库", topic_id)
        if topic_after_review:
            audit_doc_url = topic_after_review.data.get("审改文档链接", "")
            print(f"  Audit doc link: {audit_doc_url}")

    # Step 4: 小改 - 修改内容（如果需要）
    print("\n[4] Running Editor...")
    print("-" * 40)

    # 检查当前状态
    topic_before_edit = storage.get_by_id("选题库", topic_id)
    if topic_before_edit:
        current_status = topic_before_edit.data.get("状态", "")

        if current_status == "审改中":
            editor = EditorAgent(storage, llm)
            edit_result = editor.execute({"topic_id": topic_id})
            count = edit_result.get('count', 0)
            print(f"  Done: Edited {count} topics")

            # 获取修改后的状态
            topic_after_edit = storage.get_by_id("选题库", topic_id)
            if topic_after_edit:
                new_status = topic_after_edit.data.get("状态", "")
                print(f"  New status: {new_status}")
        else:
            print(f"  Status is '{current_status}', no edit needed, skipped")

    # 最终结果
    print("\n" + "=" * 60)
    print("Final Result Verification")
    print("=" * 60)

    final_topic = storage.get_by_id("选题库", topic_id)
    if final_topic:
        data = final_topic.data
        print(f"Topic title: {data.get('选题标题', 'N/A')}")
        print(f"Topic status: {data.get('状态', 'N/A')}")
        print()
        print("Document Links Check:")

        post_url = data.get('帖子文档链接', '')
        audit_url = data.get('审改文档链接', '')
        visual_scheme = data.get('配图方案', '')
        review_round = data.get('审改轮次', 0)

        print(f"  Post doc link: {post_url if post_url else 'None'}")
        print(f"  Visual scheme: {'Yes' if visual_scheme else 'No'}")
        print(f"  Audit doc link: {audit_url if audit_url else 'None'}")
        print(f"  Review round: {review_round}")
        print()

        # 验证链接格式
        if post_url:
            if "/docx/" in str(post_url):
                print("  [OK] Post doc link format correct")
            else:
                print(f"  [Warning] Post doc link format abnormal: {post_url}")

        if audit_url:
            if "/docx/" in str(audit_url):
                print("  [OK] Audit doc link format correct")
            else:
                print(f"  [Warning] Audit doc link format abnormal: {audit_url}")

    print("\n" + "=" * 60)
    print("Content production pipeline completed!")
    print("=" * 60)
    print()
    print("Please check Feishu Base [选题库] table document link fields")
    print("Post doc contains 4-platform versions (WeChat/Xiaohongshu/Douyin/Bilibili)")
    print("Audit doc contains review records and edit history")


if __name__ == "__main__":
    run_content_pipeline()
