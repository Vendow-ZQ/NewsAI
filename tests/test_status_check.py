"""检查选题状态分布"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("检查选题状态分布")
    print("="*60)

    all_topics = storage.query('选题库', limit=100)

    # Count by status
    status_count = {}
    for t in all_topics:
        status = t.data.get('状态', 'Unknown')
        status_count[status] = status_count.get(status, 0) + 1

    print("\n状态分布:")
    for status, count in status_count.items():
        print(f"  {status}: {count}个")

    # Check topics with review_round > 0
    print("\n\n审改轮次 > 0 的选题详情:")
    for t in all_topics:
        round_num = t.data.get('审改轮次', 0)
        if round_num and int(round_num) > 0:
            data = t.data
            print(f"  - {data.get('选题标题', 'N/A')[:30]}...")
            print(f"    状态: {data.get('状态')}")
            print(f"    审改轮次: {round_num}")

if __name__ == "__main__":
    main()
