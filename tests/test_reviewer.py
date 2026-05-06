"""测试Reviewer读取选题"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.interface import QueryFilter

def main():
    storage = FeishuStorage()

    print("="*60)
    print("测试Reviewer读取选题")
    print("="*60)

    # 方法1: 使用QueryFilter
    print("\n[方法1] 使用QueryFilter读取状态='生产中'或'审改中'的选题:")
    try:
        filters = [QueryFilter(field="状态", operator="in", value=["生产中", "审改中"])]
        topics1 = storage.query("选题库", filters=filters, limit=10)
        print(f"  找到 {len(topics1)} 个选题")
        for t in topics1[:3]:
            print(f"    - {t.data.get('选题标题', 'N/A')[:30]}... (状态: {t.data.get('状态', 'N/A')})")
    except Exception as e:
        print(f"  错误: {e}")

    # 方法2: 手动过滤
    print("\n[方法2] 手动过滤所有选题:")
    try:
        all_topics = storage.query("选题库", limit=100)
        valid_topics = [t for t in all_topics if t.data.get("状态") in ["生产中", "审改中"]]
        print(f"  总共 {len(all_topics)} 个选题")
        print(f"  过滤后 {len(valid_topics)} 个选题 (状态为'生产中'或'审改中')")
        for t in valid_topics[:5]:
            print(f"    - {t.data.get('选题标题', 'N/A')[:30]}... (状态: {t.data.get('状态', 'N/A')})")
    except Exception as e:
        print(f"  错误: {e}")

    # 检查所有状态分布
    print("\n[状态分布] 所有选题的状态:")
    try:
        all_topics = storage.query("选题库", limit=100)
        status_count = {}
        for topic in all_topics:
            status = topic.data.get('状态', 'Unknown')
            status_count[status] = status_count.get(status, 0) + 1

        for status, count in status_count.items():
            print(f"  {status}: {count}个")
    except Exception as e:
        print(f"  错误: {e}")

if __name__ == "__main__":
    main()
