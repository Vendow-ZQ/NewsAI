#!/usr/bin/env python3
"""创建文档 - 修复编码问题"""

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
    CreateDocumentBlockChildrenRequest,
    CreateDocumentBlockChildrenRequestBodyBuilder,
    BlockBuilder,
    TextBuilder,
    TextElementBuilder,
    TextRunBuilder,
)

app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")

print("=" * 60)
print("创建飞书文档")
print("=" * 60)

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 创建文档
try:
    print("\n创建文档...")

    body = CreateDocumentRequestBodyBuilder()
    body._title = "滚滚长江东逝水"  # 直接设置属性避免编码问题

    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(body.build())
            .build()
    )

    if resp.success():
        doc_id = resp.data.document.document_id
        print(f"[OK] 文档创建成功!")
        print(f"文档ID: {doc_id}")
        print(f"链接: https://jneyh7qlo8i.feishu.cn/docx/{doc_id}")

        # 写入内容
        print("\n写入内容...")
        text_run = TextRunBuilder().content("滚滚长江东逝水").build()
        element = TextElementBuilder().text_run(text_run).build()
        text = TextBuilder().elements([element]).build()
        block = BlockBuilder().block_type(2).text(text).build()

        resp2 = client.docx.v1.document_block_children.create(
            CreateDocumentBlockChildrenRequest.builder()
                .document_id(doc_id)
                .block_id(doc_id)
                .request_body(
                    CreateDocumentBlockChildrenRequestBodyBuilder()
                        .children([block])
                        .build()
                )
                .build()
        )

        if resp2.success():
            print("[OK] 内容写入成功!")
            print("\n文档已创建，但它在'我的文档'中")
            print("如需在Base左侧显示，需要：")
            print("1. 手动将该文档移动到Base文件夹，或")
            print("2. 在Base中创建该文档的快捷方式")
        else:
            print(f"[WARNING] 内容写入失败: {resp2.msg}")

    else:
        print(f"[FAILED] {resp.msg}")

except Exception as e:
    print(f"[EXCEPTION] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
