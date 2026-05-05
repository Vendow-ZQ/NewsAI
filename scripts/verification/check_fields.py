#!/usr/bin/env python3
"""检查选题库表字段"""

import os

# 加载 .env
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.base.tables import get_table_fields

print("[选题库表字段定义]")
print()

# 从代码中获取字段定义
fields = get_table_fields("选题库")
for field in fields:
    print(f"- {field['name']} (类型: {field['type']})")

print()
print("=" * 50)
print()

# 从飞书Base获取实际字段
storage = FeishuStorage()
print("[飞书Base实际字段]")
try:
    # 获取选题库的table_id
    from core.utils.feishu_base import FeishuBaseManager
    manager = FeishuBaseManager()

    tables = manager.list_tables()
    topic_table_id = None
    for t in tables:
        if t.get('name') == '选题库':
            topic_table_id = t.get('table_id')
            break

    if topic_table_id:
        fields_info = manager.list_fields(topic_table_id)
        for field in fields_info:
            print(f"- {field.get('field_name')} (类型: {field.get('type')})")
    else:
        print("找不到选题库表")

except Exception as e:
    print(f"获取字段失败: {e}")
    import traceback
    traceback.print_exc()
