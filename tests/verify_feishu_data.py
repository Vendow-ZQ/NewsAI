#!/usr/bin/env python3
"""验证飞书Base中的实际数据"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from core.utils.feishu_base import FeishuBaseManager

def verify_data():
    """直接查询飞书Base验证数据"""
    print("=" * 70)
    print("验证飞书Base数据")
    print("=" * 70)

    # 初始化FeishuBaseManager
    base = FeishuBaseManager()

    # 获取所有表
    print("\n[获取表列表]")
    tables = base.list_tables()
    for name, tid in tables.items():
        print(f"  - {name}: {tid}")

    # 获取选题库表ID
    if '选题库' not in tables:
        print("[错误] 选题库表不存在")
        return

    table_id = tables['选题库']
    print(f"\n选题库表ID: {table_id}")

    # 查询记录
    print("\n[查询记录]")
    records = base.list_records(table_id, page_size=5)
    print(f"  查询到 {len(records)} 条记录")

    for record in records:
        record_id = record.get('id', 'N/A')
        fields = record.get('fields', {})

        # 获取字段
        title = fields.get('选题标题', 'N/A')
        status = fields.get('状态', 'N/A')
        post_url = fields.get('帖子文档链接', '')
        audit_url = fields.get('审改文档链接', '')
        visual = fields.get('配图方案', '')
        review_round = fields.get('审改轮次', 0)

        print(f"\n  记录ID: {record_id}")
        print(f"  标题: {title}")
        print(f"  状态: {status}")
        print(f"  帖子文档链接: {post_url if post_url else '(空)'}")
        print(f"  审改文档链接: {audit_url if audit_url else '(空)'}")
        print(f"  配图方案: {(visual[:50] + '...') if visual else '(空)'}")
        print(f"  审改轮次: {review_round}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    verify_data()
