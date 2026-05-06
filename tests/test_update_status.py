"""测试直接更新选题状态"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("测试更新选题状态")
    print("="*60)

    # Get a topic with status="审改中"
    all_topics = storage.query("选题库", limit=100)
    reviewing_topics = [t for t in all_topics if t.data.get("状态") == "审改中"]

    if not reviewing_topics:
        print("没有找到状态为'审改中'的选题")
        return

    topic = reviewing_topics[0]
    topic_id = topic.data.get("id")
    old_status = topic.data.get("状态")

    print(f"\n选题ID: {topic_id}")
    print(f"原标题: {topic.data.get('选题标题', 'N/A')[:30]}...")
    print(f"原状态: {old_status}")
    print(f"原审改轮次: {topic.data.get('审改轮次', 0)}")

    # Try to update status to "生产中"
    print("\n尝试更新状态为'生产中'...")
    try:
        update_data = {"状态": "生产中"}
        result = storage.update("选题库", topic_id, update_data)
        print(f"更新结果: {result}")

        # Verify the update
        updated = storage.get_by_id("选题库", topic_id)
        new_status = updated.data.get("状态")
        print(f"\n更新后状态: {new_status}")

        if new_status == "生产中":
            print("✓ 状态更新成功！")
        else:
            print("✗ 状态更新失败")
    except Exception as e:
        print(f"更新失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
