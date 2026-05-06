"""直接创建数据库记录，模拟 Analyst 的产出"""
import os
from dotenv import load_dotenv

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.id_generator import IDGenerator
from datetime import datetime
import random

def main():
    storage = FeishuStorage()

    print("="*60)
    print("直接创建数据库记录")
    print("="*60)

    # 获取所有选题
    all_topics = storage.query("选题库", limit=100)

    # 获取有文档链接的选题
    topics_with_docs = [
        t for t in all_topics
        if t.data.get("帖子文档链接") or t.data.get("视频脚本文档链接")
    ][:5]

    print(f"\n找到 {len(topics_with_docs)} 个有文档的选题")

    created_count = 0
    for topic in topics_with_docs:
        topic_id = topic.data.get("id")
        topic_title = topic.data.get("选题标题", "N/A")[:30]

        # 生成模拟数据
        base_score = random.uniform(0.3, 0.9)
        record_data = {
            "id": IDGenerator.generate("DATA"),
            "选题ID": topic_id,
            "选题标题": topic.data.get("选题标题", ""),
            "公众号_阅读量": int(random.uniform(1000, 100000)),
            "公众号_点赞数": int(random.uniform(50, 5000)),
            "公众号_在看数": int(random.uniform(20, 2000)),
            "小红书_阅读量": int(random.uniform(2000, 150000)),
            "小红书_点赞数": int(random.uniform(100, 8000)),
            "小红书_收藏数": int(random.uniform(50, 5000)),
            "小红书_评论数": int(random.uniform(10, 500)),
            "抖音_播放量": int(random.uniform(5000, 2000000)),
            "抖音_点赞数": int(random.uniform(200, 100000)),
            "抖音_评论数": int(random.uniform(50, 3000)),
            "B站_播放量": int(random.uniform(3000, 800000)),
            "B站_点赞数": int(random.uniform(150, 50000)),
            "B站_投币数": int(random.uniform(30, 10000)),
            "综合评分": round(base_score, 2),
            "爆点验证": random.choice(["验证成功", "部分验证", "未爆"]),
            "数据采集时间": int(datetime.now().timestamp() * 1000),
            "数据状态": "已迭代分析",
        }

        try:
            storage.create("数据库", record_data)
            print(f"OK {topic_title}... ->数据库")
            created_count += 1
        except Exception as e:
            print(f"FAIL {topic_title}... 创建失败: {e}")

    print(f"\n完成！创建了 {created_count} 条数据库记录。")

if __name__ == "__main__":
    main()
