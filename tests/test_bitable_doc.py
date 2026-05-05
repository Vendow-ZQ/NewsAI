#!/usr/bin/env python3
"""测试 Bitable 文档字段写入"""

import os
import sys

# 加载 .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.base.tables import get_table_fields

# 初始化 storage
storage = FeishuStorage()

print("[测试 Bitable 文档字段]")
print()

# 测试：更新一条选题记录，写入文档字段
topic_id = "TOPIC-20260504-001"  # 假设存在这条记录

# 测试内容（Markdown格式）
test_doc_content = """# 测试文档标题

滚滚长江东逝水

## 第二段
123123

456456

789789
"""

try:
    # 尝试更新选题的帖子内容字段（文档类型）
    update_data = {
        "帖子内容": test_doc_content,
    }

    storage.update("选题库", topic_id, update_data)
    print(f"[OK] 文档写入成功")
    print(f"     选题ID: {topic_id}")
    print(f"     内容预览: {test_doc_content[:50]}...")

except Exception as e:
    print(f"[FAILED] 文档写入失败: {e}")
    print(f"\n可能原因:")
    print(f"1. 选题 {topic_id} 不存在 - 需要先运行 bootstrap.py 创建表和种子数据")
    print(f"2. 字段类型不匹配 - 需要重新创建表")
    print(f"3. 飞书API权限问题")

print()
print("[建议]")
print("如果测试失败，需要先:")
print("1. 删除现有的飞书 Base 表")
print("2. 重新运行 bootstrap.py 创建表（使用新的文档字段类型）")
print("3. 再运行此测试")
