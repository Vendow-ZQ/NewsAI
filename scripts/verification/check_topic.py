#!/usr/bin/env python3
"""检查选题记录"""

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

storage = FeishuStorage()

# 查询选题记录
topics = storage.query('选题库', limit=5)
print(f"找到 {len(topics)} 条选题记录")
print()

for i, topic in enumerate(topics):
    data = topic.data
    print(f"{i+1}. {data.get('选题标题', '无标题')}")
    print(f"   ID: {data.get('id', '')}")
    print(f"   状态: {data.get('状态', '')}")
    print()
