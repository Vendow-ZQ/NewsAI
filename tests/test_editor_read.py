"""测试Editor读取选题"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("测试Editor读取选题")
    print("="*60)

    # 手动过滤避免QueryFilter问题
    all_topics = storage.query("选题库", limit=100)
    topics = [t for t in all_topics if t.data.get("状态") == "审改中"][:10]

    print(f"\n找到 {len(topics)} 个状态为'审改中'的选题")
    for t in topics[:5]:
        data = t.data
        print(f"  - {data.get('选题标题', 'N/A')[:30]}...")
        print(f"    ID: {data.get('id', 'N/A')}")
        print(f"    审改轮次: {data.get('审改轮次', 0)}")
        print(f"    审改文档链接: {'有' if data.get('审改文档链接') else '无'}")
        print()

if __name__ == "__main__":
    main()
