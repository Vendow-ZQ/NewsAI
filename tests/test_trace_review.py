"""Trace the review flow"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("追踪Review流程")
    print("="*60)

    # Get topics that Reviewer would process
    all_topics = storage.query("选题库", limit=100)

    valid_status = ["生产中", "审改中"]
    filtered_topics = [t for t in all_topics if t.data.get("状态") in valid_status]

    print(f"\n1. Reviewer读取 {len(filtered_topics)} 个选题 (状态为'生产中'或'审改中')")

    # Simulate _is_already_reviewed filtering
    valid_topics = []
    for topic in filtered_topics:
        topic_data = topic.data
        status = topic_data.get("状态", "")
        review_round = topic_data.get("审改轮次", 0)

        if status == "审改中" and review_round and int(review_round) > 0:
            print(f"   过滤掉: {topic_data.get('选题标题', 'N/A')[:20]}... (状态:{status}, 轮次:{review_round}) - 已审查等待修改")
        else:
            valid_topics.append(topic_data)

    print(f"\n2. 过滤后剩 {len(valid_topics)} 个选题需要审查")

    for topic in valid_topics[:3]:
        status = topic.get("状态", "")
        review_round = topic.get("审改轮次", 0)

        # Simulate current_round calculation
        if status == "生产中":
            current_round = 1
        else:
            current_round = int(review_round) + 1 if review_round else 1

        print(f"\n   选题: {topic.get('选题标题', 'N/A')[:30]}...")
        print(f"   - 当前状态: {status}")
        print(f"   - 数据库轮次: {review_round}")
        print(f"   - 本次审查轮次: {current_round}")

        if current_round >= 2:
            print(f"   - 结果: 强制通过（达到第2轮）")
        else:
            print(f"   - 结果: 正常审查（第1轮）")

if __name__ == "__main__":
    main()
