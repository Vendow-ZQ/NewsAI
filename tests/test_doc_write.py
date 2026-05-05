#!/usr/bin/env python3
"""测试 Bitable 文档字段写入"""

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

print("[测试 Bitable 文档字段写入]")
print()

# 使用第一条选题记录
topic_id = "TOPIC-20260505-002"

# 测试内容（Markdown格式）
test_content = """# 滚滚长江东逝水

## 第一段
123123

## 第二段
456456

## 第三段
789789
"""

try:
    update_data = {
        "帖子内容": test_content,
        "状态": "生产中"
    }

    storage.update("选题库", topic_id, update_data)
    print("[OK] 文档写入成功!")
    print(f"     选题ID: {topic_id}")
    print(f"     字段: 帖子内容")
    print()
    print("内容预览:")
    print(test_content[:100] + "...")

except Exception as e:
    print(f"[FAILED] {e}")
    import traceback
    traceback.print_exc()
