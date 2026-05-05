#!/usr/bin/env python3
"""测试飞书文档创建 - 最小可用示例"""

import os
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

# 从 .env 文件加载环境变量
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# 从环境变量读取凭证
app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")

print(f"App ID: {app_id[:6]}..." if app_id else "App ID: None")
print(f"App Secret: {app_secret[:6]}..." if app_secret else "App Secret: None")

if not app_id or not app_secret:
    print("[ERROR] 缺少飞书应用凭证")
    exit(1)

# 创建客户端
client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

print("\n[创建飞书文档...]")

# 1. 创建空白文档
try:
    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(
                CreateDocumentRequestBodyBuilder()
                    .title("测试文档")
                    .build()
            )
            .build()
    )

    if not resp.success():
        print(f"[FAILED] 创建文档失败: {resp.msg}")
        print(f"错误码: {resp.code}")
        exit(1)

    doc_id = resp.data.document.document_id
    print(f"[OK] 文档创建成功")
    print(f"     文档ID: {doc_id}")

except Exception as e:
    print(f"[FAILED] 创建文档异常: {e}")
    exit(1)

# 2. 写入内容
try:
    # 构造文本Block
    text_run = TextRunBuilder().content("滚滚长江东逝水").build()
    element = TextElementBuilder().text_run(text_run).build()
    text = TextBuilder().elements([element]).build()
    block = BlockBuilder().block_type(2).text(text).build()  # type=2 是普通文本

    resp = client.docx.v1.document_block_children.create(
        CreateDocumentBlockChildrenRequest.builder()
            .document_id(doc_id)
            .block_id(doc_id)  # 根block_id就是document_id
            .request_body(
                CreateDocumentBlockChildrenRequestBodyBuilder()
                    .children([block])
                    .build()
            )
            .build()
    )

    if not resp.success():
        print(f"[FAILED] 写入内容失败: {resp.msg}")
        exit(1)

    print(f"[OK] 内容写入成功")

except Exception as e:
    print(f"[FAILED] 写入内容异常: {e}")
    exit(1)

# 3. 输出文档链接
doc_url = f"https://jneyh7qlo8i.feishu.cn/docx/{doc_id}"
print(f"\n[DONE] 测试完成！")
print(f"       文档标题: 测试文档")
print(f"       文档内容: 滚滚长江东逝水")
print(f"       文档链接: {doc_url}")
