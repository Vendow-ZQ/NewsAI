#!/usr/bin/env python3
"""在指定folder中创建文档"""

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

# 从用户输入获取folder_token
print("=" * 60)
print("在Base中创建文档")
print("=" * 60)
print()
print("请从浏览器获取folder_token：")
print("1. 打开飞书，进入云文档")
print("2. 找到包含这个Base的文件夹")
print("3. 复制URL中 folder/ 后面的部分")
print()
print("例如：https://jneyh7qlo8i.feishu.cn/drive/folder/AbCdEfGh123")
print("     folder_token = AbCdEfGh123")
print()

# 尝试从文件读取，否则使用默认值
folder_token = ""
if os.path.exists('.folder_token'):
    with open('.folder_token', 'r') as f:
        folder_token = f.read().strip()
        print(f"从文件读取到folder_token: {folder_token[:15]}...")
else:
    folder_token = input("请输入folder_token（或按回车跳过）: ").strip()

if not folder_token:
    print("\n没有folder_token，无法创建到指定文件夹")
    print("将创建到默认位置（我的文档）")

# 创建客户端
client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 创建文档
print("\n创建文档...")

try:
    builder = CreateDocumentRequestBodyBuilder().title("滚滚长江东逝水")
    if folder_token:
        builder = builder.folder_token(folder_token)

    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(builder.build())
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
        else:
            print(f"[WARNING] 内容写入失败: {resp2.msg}")

    else:
        print(f"[FAILED] {resp.msg}")

except Exception as e:
    print(f"[EXCEPTION] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
