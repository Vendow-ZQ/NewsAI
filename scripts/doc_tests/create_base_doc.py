#!/usr/bin/env python3
"""在Base内部创建文档"""

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

from lark_oapi import Client
from lark_oapi.api.docx.v1 import (
    CreateDocumentRequest,
    CreateDocumentRequestBodyBuilder,
)
from lark_oapi.api.drive.v1 import (
    CreateShortcutRequest,
    CreateShortcutRequestBodyBuilder,
)

app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")
base_token = os.getenv("LARK_BASE_APP_TOKEN")  # Base的token

print(f"App ID: {app_id[:6]}...")
print(f"Base Token: {base_token[:6]}...")

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 方法1: 创建文档并指定folder_token（Base的folder）
print("\n[尝试在Base中创建文档...]")

# 需要先获取Base对应的folder_token
# Base的URL格式: https://base.feishu.cn/RaFQbhb74aqFigsjqBEcQ0ZInHd
# 最后一部分是base_token

# 创建空白文档
try:
    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(
                CreateDocumentRequestBodyBuilder()
                    .title("帖子内容测试文档")
                    # .folder_token(folder_token)  # 需要Base的folder_token
                    .build()
            )
            .build()
    )

    if resp.success():
        doc_id = resp.data.document.document_id
        print(f"[OK] 文档创建成功")
        print(f"     文档ID: {doc_id}")
        print(f"     链接: https://jneyh7qlo8i.feishu.cn/docx/{doc_id}")
        print("\n[注意] 这个文档在Base外部，需要手动移动到Base中")
    else:
        print(f"[FAILED] {resp.msg}")

except Exception as e:
    print(f"[FAILED] {e}")

print("\n" + "="*50)
print("结论: 飞书API目前无法直接在Base内部创建文档")
print("解决方案: 使用Bitable的'文档'字段类型代替")
print("="*50)
