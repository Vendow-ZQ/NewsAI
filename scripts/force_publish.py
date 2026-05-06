"""强制发布选题 - 将审改完成的选题直接设为待发布"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("强制发布选题")
    print("="*60)

    # 获取审改轮次>=1的选题
    all_topics = storage.query("选题库", limit=100)
    reviewing_topics = [
        t for t in all_topics
        if t.data.get("审改轮次") and int(t.data.get("审改轮次")) >= 1
    ][:10]

    print(f"\n找到 {len(reviewing_topics)} 个需要强制发布的选题")

    for topic in reviewing_topics:
        topic_id = topic.data.get("id")
        title = topic.data.get("选题标题", "N/A")[:30]

        # 将状态更新为"待发布"
        try:
            storage.update("选题库", topic_id, {"状态": "待发布"})
            print(f"OK {title}... ->待发布")
        except Exception as e:
            print(f"FAIL {title}... 更新失败: {e}")

    print("\n完成！现在运行工作流程，Distributor会处理这些选题。")

if __name__ == "__main__":
    main()
