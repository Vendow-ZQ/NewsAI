"""诊断脚本 - 检查Base中各表的状态"""
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.interface import QueryFilter

def main():
    print("="*60)
    print("NewsAI Base 状态诊断")
    print("="*60)

    storage = FeishuStorage()

    # 1. 检查选题库
    print("\n[1] 选题库状态统计")
    try:
        # 获取所有选题
        all_topics = storage.query("选题库", limit=100)
        print(f"   总选题数: {len(all_topics)}")

        # 按状态统计
        status_count = {}
        for topic in all_topics:
            data = topic.data
            status = data.get('状态', 'Unknown')
            status_count[status] = status_count.get(status, 0) + 1

        for status, count in status_count.items():
            print(f"   - {status}: {count}条")

        # 显示前5条详细信息
        print("\n   前5条选题详情:")
        for i, topic in enumerate(all_topics[:5], 1):
            data = topic.data
            print(f"   {i}. {data.get('选题标题', 'N/A')[:30]}...")
            print(f"      ID: {data.get('id', 'N/A')}")
            print(f"      状态: {data.get('状态', 'N/A')}")
            print(f"      审改轮次: {data.get('审改轮次', 'N/A')}")
            print(f"      帖子文档链接: {'有' if data.get('帖子文档链接') else '无'}")
            print(f"      视频脚本文档链接: {'有' if data.get('视频脚本文档链接') else '无'}")

    except Exception as e:
        print(f"   错误: {e}")

    # 2. 检查数据库（小数的产出）
    print("\n[2] 数据库记录数")
    try:
        all_data = storage.query("数据库", limit=100)
        print(f"   总记录数: {len(all_data)}")

        if all_data:
            print("\n   前3条数据分析:")
            for i, data in enumerate(all_data[:3], 1):
                d = data.data
                print(f"   {i}. {d.get('选题标题', 'N/A')[:30]}...")
                print(f"      综合评分: {d.get('综合评分', 'N/A')}")
                print(f"      经验文档链接: {'有' if d.get('经验文档链接') else '无'}")
    except Exception as e:
        print(f"   错误: {e}")

    # 3. 检查Agent协作日志
    print("\n[3] Agent协作日志")
    try:
        all_logs = storage.query("Agent协作日志", limit=100)
        print(f"   总记录数: {len(all_logs)}")

        if all_logs:
            # 按Agent统计
            agent_count = {}
            for log in all_logs:
                agent = log.data.get('Agent花名', 'Unknown')
                agent_count[agent] = agent_count.get(agent, 0) + 1

            print("\n   各Agent日志数:")
            for agent, count in agent_count.items():
                print(f"   - {agent}: {count}条")
        else:
            print("   [警告] Agent协作日志为空！")
    except Exception as e:
        print(f"   错误: {e}")
        print(f"   [警告] 无法读取Agent协作日志")

    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)

if __name__ == "__main__":
    main()
