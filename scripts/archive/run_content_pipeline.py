#!/usr/bin/env python3
"""内容生产流水线 - 运行小文、小图、小审、小改"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter
from datetime import datetime

# 导入Agent
from core.agents.content_writer import ContentWriterAgent
from core.agents.visual_designer import VisualDesignerAgent
from core.agents.reviewer import ReviewerAgent
from core.agents.editor import EditorAgent


def run_content_pipeline():
    """运行内容生产全流程"""
    print("=" * 60)
    print("NewsAI 内容生产流水线")
    print("=" * 60)

    # 初始化存储和LLM
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    llm = get_llm()

    # 找一个待生产的选题（已选状态）
    print("\n[0] 查找待生产的选题...")
    all_topics = storage.query("选题库", limit=100)
    pending_topics = [t for t in all_topics if t.data.get("状态") == "已选"]

    if not pending_topics:
        print("  没有找到状态为'已选'的选题，请先运行小编生成选题")
        return

    topic = pending_topics[-1].data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "未命名")
    print(f"  选中选题: {topic_title}")
    print(f"  选题ID: {topic_id}")

    # Step 1: 小文 - 生成内容并创建飞书文档
    print("\n[1] 运行小文 (ContentWriter)...")
    print("-" * 40)

    writer = ContentWriterAgent(storage, llm)
    writer_result = writer.execute({"topic_ids": [topic_id]})

    print(f"  ✓ 完成：撰写 {writer_result.get('count', 0)} 条选题的4平台版本")

    # 获取生成的文档链接
    topic_updated = storage.get_by_id("选题库", topic_id)
    post_doc_url = topic_updated.data.get("帖子文档链接", "")
    print(f"  ✓ 帖子文档链接: {post_doc_url}")

    # Step 2: 小图 - 生成配图方案
    print("\n[2] 运行小图 (VisualDesigner)...")
    print("-" * 40)

    visual = VisualDesignerAgent(storage, llm)
    visual_result = visual.execute({"topic_id": topic_id})

    print(f"  ✓ 完成：为 {visual_result.get('count', 0)} 个选题生成配图方案")
    designs = visual_result.get("designs", [])
    if designs:
        design = designs[0]
        print(f"  ✓ 配图方案: {len(design.get('配图方案', []))} 张图")
        print(f"  ✓ 视觉风格: {design.get('视觉风格', '')}")

    # Step 3: 小审 - 审查内容并创建审改文档
    print("\n[3] 运行小审 (Reviewer)...")
    print("-" * 40)

    reviewer = ReviewerAgent(storage, llm)
    review_result = reviewer.execute({"topic_id": topic_id})

    reviews = review_result.get("review_results", [])
    if reviews:
        review = reviews[0]
        review_data = review.get("review_result", {})
        conclusion = review_data.get("审查结论", "未知")
        print(f"  ✓ 审查结论: {conclusion}")
        print(f"  ✓ 严重度: {review_data.get('严重度', '未知')}")
        print(f"  ✓ 发现问题: {len(review_data.get('发现的问题', []))} 处")

        # 获取审改文档链接
        topic_after_review = storage.get_by_id("选题库", topic_id)
        audit_doc_url = topic_after_review.data.get("审改文档链接", "")
        print(f"  ✓ 审改文档链接: {audit_doc_url}")

    # Step 4: 小改 - 修改内容（如果需要）
    print("\n[4] 运行小改 (Editor)...")
    print("-" * 40)

    # 检查当前状态
    topic_before_edit = storage.get_by_id("选题库", topic_id)
    current_status = topic_before_edit.data.get("状态", "")

    if current_status == "审改中":
        editor = EditorAgent(storage, llm)
        edit_result = editor.execute({"topic_id": topic_id})
        print(f"  ✓ 完成：修改 {edit_result.get('count', 0)} 条选题")

        # 获取修改后的状态
        topic_after_edit = storage.get_by_id("选题库", topic_id)
        new_status = topic_after_edit.data.get("状态", "")
        print(f"  ✓ 修改后状态: {new_status}")
    else:
        print(f"  状态为 '{current_status}'，无需修改，跳过")

    # 最终结果
    print("\n" + "=" * 60)
    print("最终结果验证")
    print("=" * 60)

    final_topic = storage.get_by_id("选题库", topic_id)
    if final_topic:
        data = final_topic.data
        print(f"选题标题: {data.get('选题标题', 'N/A')}")
        print(f"选题状态: {data.get('状态', 'N/A')}")
        print()
        print("【文档链接】字段检查:")
        print(f"  📄 帖子文档链接: {data.get('帖子文档链接', '❌ 无')}")
        print(f"  🎨 配图方案: {'✅ 有' if data.get('配图方案') else '❌ 无'}")
        print(f"  🔍 审改文档链接: {data.get('审改文档链接', '❌ 无')}")
        print(f"  📝 审改轮次: {data.get('审改轮次', 0)}")
        print()

        # 验证链接格式
        post_url = data.get("帖子文档链接", "")
        audit_url = data.get("审改文档链接", "")

        if post_url:
            if "/docx/" in str(post_url):
                print("  ✅ 帖子文档链接格式正确")
            else:
                print(f"  ⚠️ 帖子文档链接格式异常: {post_url}")

        if audit_url:
            if "/docx/" in str(audit_url):
                print("  ✅ 审改文档链接格式正确")
            else:
                print(f"  ⚠️ 审改文档链接格式异常: {audit_url}")

    print("\n" + "=" * 60)
    print("内容生产流水线运行完成！")
    print("=" * 60)
    print()
    print("📌 请检查飞书多维表格【选题库】中的文档链接字段")
    print("📌 帖子文档包含4平台版本内容（公众号/小红书/抖音/B站）")
    print("📌 审改文档包含审查记录和修改历史")


if __name__ == "__main__":
    run_content_pipeline()
