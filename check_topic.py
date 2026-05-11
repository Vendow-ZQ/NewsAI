#!/usr/bin/env python3
"""检查特定选题的文档链接"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def check_topic():
    storage = FeishuStorage()

    # 查找TOPIC-20260507-004
    topic_id = "TOPIC-20260507-004"

    print(f"Checking topic: {topic_id}")
    print("=" * 70)

    topic = storage.get_by_id("选题库", topic_id)
    if topic:
        data = topic.data
        print(f"\nTopic Title: {data.get('选题标题', 'N/A')}")
        print(f"Status: {data.get('状态', 'N/A')}")
        print()

        post_url = data.get('帖子文档链接', '')
        audit_url = data.get('审改文档链接', '')

        post_url_str = post_url.get('link', '') if isinstance(post_url, dict) else post_url
        audit_url_str = audit_url.get('link', '') if isinstance(audit_url, dict) else audit_url

        print(f"Post Doc Link: {post_url_str if post_url_str else '(empty)'}")
        print(f"Audit Doc Link: {audit_url_str if audit_url_str else '(empty)'}")
        print(f"Visual Style: {data.get('视觉风格', 'N/A')}")
        print(f"Review Round: {data.get('审改轮次', 0)}")

        # 检查配图方案
        visual = data.get('配图方案', '')
        if visual:
            print(f"\nVisual Scheme: {visual[:200]}...")
        else:
            print(f"\nVisual Scheme: (empty)")

        print("\n" + "=" * 70)
        print("Check the documents:")
        if post_url_str:
            print(f"Post Doc: {post_url_str}")
        if audit_url_str:
            print(f"Audit Doc: {audit_url_str}")
    else:
        print(f"Topic {topic_id} not found")

if __name__ == "__main__":
    check_topic()
