"""测试Distributor读取选题"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("测试Distributor读取选题")
    print("="*60)

    # 方法1: 使用QueryFilter
    print("\n[方法1] 使用QueryFilter读取状态='待发布'的选题:")
    try:
        from core.storage.interface import QueryFilter
        filters = [QueryFilter(field="状态", operator="eq", value="待发布")]
        topics1 = storage.query("选题库", filters=filters, limit=10)
        print(f"  找到 {len(topics1)} 个选题")
    except Exception as e:
        print(f"  错误: {e}")

    # 方法2: 手动过滤
    print("\n[方法2] 手动过滤读取状态='待发布'的选题:")
    try:
        all_topics = storage.query("选题库", limit=100)
        topics2 = [t for t in all_topics if t.data.get("状态") == "待发布"][:10]
        print(f"  找到 {len(topics2)} 个选题")
        for t in topics2[:5]:
            print(f"    - {t.data.get('选题标题', 'N/A')[:30]}...")
    except Exception as e:
        print(f"  错误: {e}")

if __name__ == "__main__":
    main()
