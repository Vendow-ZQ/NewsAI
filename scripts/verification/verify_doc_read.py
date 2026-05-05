#!/usr/bin/env python3
"""验证文档字段读取"""

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

print("[验证文档字段读取]")
print()

topic_id = "TOPIC-20260505-002"

# 读取记录
record = storage.get_by_id("选题库", topic_id)
if record:
    data = record.data
    print(f"选题标题: {data.get('选题标题', '')}")
    print(f"状态: {data.get('状态', '')}")
    print()

    post_content = data.get('帖子内容', '')
    if post_content:
        print("帖子内容字段已写入!")
        print("="*50)
        print(post_content[:200])
        print("="*50)
        print(f"\n总长度: {len(post_content)} 字符")
    else:
        print("帖子内容字段为空")
else:
    print(f"记录不存在: {topic_id}")
