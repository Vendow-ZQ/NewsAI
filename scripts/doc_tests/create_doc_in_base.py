#!/usr/bin/env python3
"""在Base内部创建文档（左侧显示）"""

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

app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")
base_token = os.getenv("LARK_BASE_APP_TOKEN")

print("=" * 60)
print("在Base内部创建文档")
print("=" * 60)

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 使用Base的app_token作为folder_token创建文档
print("\n尝试在Base中创建文档...")
print(f"Base Token: {base_token[:10]}...")

try:
    # 创建文档，使用base_token作为folder_token
    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(
                CreateDocumentRequestBodyBuilder()
                    .title("测试文档-滚滚长江东逝水")
                    .folder_token(base_token)  # 使用Base的token作为folder
                    .build()
            )
            .build()
    )

    if resp.success():
        doc_id = resp.data.document.document_id
        print(f"[OK] 文档创建成功!")
        print(f"文档ID: {doc_id}")
        print(f"链接: https://jneyh7qlo8i.feishu.cn/docx/{doc_id}")
    else:
        print(f"[FAILED] {resp.msg}")
        print(f"错误码: {resp.code}")

except Exception as e:
    print(f"[EXCEPTION] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
