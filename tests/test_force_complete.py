"""强制完成审改循环 - 将待审改选题改为生产中，让Reviewer重新审查"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("强制完成审改循环")
    print("="*60)

    # 获取审改轮次>=1的选题（无论状态）
    all_topics = storage.query("选题库", limit=100)
    reviewing_topics = [
        t for t in all_topics
        if t.data.get("审改轮次") and int(t.data.get("审改轮次")) >= 1
    ][:10]  # 只处理前10个

    print(f"\n找到 {len(reviewing_topics)} 个需要强制完成的选题")

    for topic in reviewing_topics:
        topic_id = topic.data.get("id")
        title = topic.data.get("选题标题", "N/A")[:30]

        # 将状态更新为"生产中"，让Reviewer重新审查
        try:
            storage.update("选题库", topic_id, {"状态": "生产中"})
            print(f"OK {title}... ->生产中")
        except Exception as e:
            print(f"FAIL {title}... 更新失败: {e}")

    print("\n完成！现在运行工作流程，Reviewer会重新审查这些选题并强制通过。")

if __name__ == "__main__":
    main()
