"""检查选题的审改轮次状态"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("检查选题审改轮次")
    print("="*60)

    # Check topics with review_round > 0
    all_topics = storage.query('选题库', limit=100)
    reviewing_topics = [t for t in all_topics if t.data.get('审改轮次') and int(t.data.get('审改轮次')) > 0]

    print(f"\n总共有 {len(reviewing_topics)} 个选题的审改轮次 > 0")
    print("\n前10个选题:")
    for t in reviewing_topics[:10]:
        data = t.data
        print(f"  - {data.get('选题标题', 'N/A')[:30]}...")
        print(f"    状态: {data.get('状态')}")
        print(f"    审改轮次: {data.get('审改轮次')}")
        print(f"    审改文档链接: {'有' if data.get('审改文档链接') else '无'}")
        print()

if __name__ == "__main__":
    main()
