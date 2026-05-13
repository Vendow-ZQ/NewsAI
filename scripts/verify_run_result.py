"""验证最近一次运行的结果

检查飞书Base中的数据状态，确认各Agent是否正常执行。
"""

import sys
sys.path.insert(0, 'D:\\Code\\NewsAI')

from core.utils.feishu_base import FeishuBaseManager
from datetime import datetime

def verify_results():
    print("=" * 60)
    print("NewsAI 运行结果验证")
    print("=" * 60)

    try:
        base = FeishuBaseManager()

        # 1. 检查热帖库
        print("\n[1] 热帖库检查")
        trends = base.list_records("热帖库")
        print(f"   记录数: {len(trends)}")
        if trends:
            print(f"   最新记录: {trends[0].get('标题', 'N/A')[:30]}...")
            print(f"   状态分布: {count_by_status(trends, '状态')}")

        # 2. 检查选题库
        print("\n[2] 选题库检查")
        topics = base.list_records("选题库")
        print(f"   记录数: {len(topics)}")
        if topics:
            print(f"   状态分布: {count_by_status(topics, '选题状态')}")
            for topic in topics[:3]:
                print(f"   - {topic.get('选题标题', 'N/A')[:20]}... ({topic.get('选题状态', 'N/A')})")

        # 3. 检查内容资产库
        print("\n[3] 内容资产库检查")
        assets = base.list_records("内容资产库")
        print(f"   记录数: {len(assets)}")
        if assets:
            for asset in assets[:3]:
                print(f"   - ASSET: 文案{asset.get('文案状态', 'N/A')}/配图{asset.get('配图状态', 'N/A')}/视频{asset.get('视频状态', 'N/A')}")
                if asset.get('文案文档链接'):
                    print(f"     文案文档: ✅")
                if asset.get('审改文档链接'):
                    print(f"     审改文档: ✅ ({asset.get('审改状态', 'N/A')})")

        # 4. 检查数据库
        print("\n[4] 数据库检查")
        data_records = base.list_records("数据库")
        print(f"   记录数: {len(data_records)}")
        if data_records:
            for record in data_records[:2]:
                print(f"   - 评分: {record.get('综合评分', 'N/A')}, 验证: {record.get('爆点验证', 'N/A')}")

        # 5. 检查Agent协作日志
        print("\n[5] Agent协作日志检查")
        logs = base.list_records("Agent协作日志")
        print(f"   记录数: {len(logs)}")

        # 统计最近执行的Agent
        agent_counts = {}
        for log in logs[-20:]:  # 最近20条
            agent_name = log.get('Agent花名', 'Unknown')
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1

        print("   最近执行记录:")
        for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {agent}: {count}次")

        print("\n" + "=" * 60)
        print("验证完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

def count_by_status(records, status_field):
    """统计状态分布"""
    counts = {}
    for record in records:
        status = record.get(status_field, 'Unknown')
        counts[status] = counts.get(status, 0) + 1
    return counts

if __name__ == "__main__":
    verify_results()
