#!/usr/bin/env python3
"""调试脚本 - 检查字段类型和数据"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage

def debug_table_fields():
    """调试表字段"""
    print("=" * 70)
    print("调试飞书表字段")
    print("=" * 70)

    storage = FeishuStorage()

    # 获取选题库的表ID
    table_id = storage._get_table_id("选题库")
    print(f"\n选题库 table_id: {table_id}")

    # 获取字段信息
    fields = storage._get_table_fields(table_id)
    print(f"\n字段列表 ({len(fields)} 个):")
    for field in fields:
        field_name = field.get('name', '')
        field_type = field.get('type', 0)
        print(f"  - {field_name}: type={field_type}")

    # 查找包含"文档"的字段
    print("\n包含'文档'的字段:")
    for field in fields:
        field_name = field.get('name', '')
        if '文档' in field_name:
            field_type = field.get('type', 0)
            print(f"  - {field_name}: type={field_type}")

    # 查询几条记录查看实际数据
    print("\n查询实际记录数据:")
    records = storage.query("选题库", limit=3)
    for record in records:
        data = record.data
        record_id = data.get('id', 'N/A')
        title = data.get('选题标题', 'N/A')[:20]

        print(f"\n  记录ID: {record_id}")
        print(f"  标题: {title}")

        post_url = data.get('帖子文档链接', '')
        audit_url = data.get('审改文档链接', '')

        print(f"  帖子文档链接: {post_url}")
        print(f"    类型: {type(post_url)}")

        print(f"  审改文档链接: {audit_url}")
        print(f"    类型: {type(audit_url)}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    debug_table_fields()
