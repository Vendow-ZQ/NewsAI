"""强制分析选题 - 将待发布选题设为已发布并设置发布时间"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def main():
    storage = FeishuStorage()

    print("="*60)
    print("强制发布并分析选题")
    print("="*60)

    # 获取所有选题
    all_topics = storage.query("选题库", limit=100)

    # 获取需要发布的选题（有文档链接的）
    topics_to_publish = []
    for t in all_topics:
        data = t.data
        if data.get("帖子文档链接") or data.get("视频脚本文档链接"):
            topics_to_publish.append(t)

    print(f"\n找到 {len(topics_to_publish)} 个有文档的选题")

    # 发布前5个
    for topic in topics_to_publish[:5]:
        topic_id = topic.data.get("id")
        title = topic.data.get("选题标题", "N/A")[:30]

        # 设置为已发布，发布时间设为25小时前（让Analyst能处理）
        import time
        publish_time = int((time.time() - 25*3600) * 1000)  # 25小时前

        try:
            storage.update("选题库", topic_id, {
                "状态": "已发布",
                "发布完成时间": publish_time
            })
            print(f"OK {title}... -> 已发布 (25小时前)")
        except Exception as e:
            print(f"FAIL {title}... 更新失败: {e}")

    print("\n完成！现在 Analyst 会处理这些选题。")

if __name__ == "__main__":
    main()
