#!/usr/bin/env python3
"""在云文档根目录创建文档（Base旁边）"""

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
print("在Base旁边创建4个文档")
print("=" * 60)

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 文档列表
docs = [
    ("帖子内容", "这是小文生成的帖子内容文档\n\n滚滚长江东逝水"),
    ("视频脚本", "这是小播生成的视频脚本文档\n\n123123\n456456\n789789"),
    ("审改记录", "这是小审和小改维护的审改记录\n\n第一轮审查：通过"),
    ("经验总结", "这是小数生成的经验总结\n\n本月数据分析..."),
]

created_docs = []

for title, content in docs:
    try:
        print(f"\n创建文档: {title}...")

        # 创建文档（不指定folder_token，创建到默认位置）
        body = CreateDocumentRequestBodyBuilder()
        body._title = title

        resp = client.docx.v1.document.create(
            CreateDocumentRequest.builder()
                .request_body(body.build())
                .build()
        )

        if resp.success():
            doc_id = resp.data.document.document_id
            doc_url = f"https://jneyh7qlo8i.feishu.cn/docx/{doc_id}"
            print(f"  [OK] 创建成功")
            print(f"       ID: {doc_id}")
            print(f"       URL: {doc_url}")

            # 写入内容
            text_run = TextRunBuilder().content(content).build()
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
                print(f"  [OK] 内容写入成功")
            else:
                print(f"  [WARN] 内容写入失败: {resp2.msg}")

            created_docs.append((title, doc_id, doc_url))
        else:
            print(f"  [FAILED] {resp.msg}")

    except Exception as e:
        print(f"  [EXCEPTION] {e}")

print("\n" + "=" * 60)
print("创建的文档列表:")
print("=" * 60)
for title, doc_id, url in created_docs:
    print(f"\n{title}:")
    print(f"  ID: {doc_id}")
    print(f"  URL: {url}")

print("\n" + "=" * 60)
print("注意: 这些文档现在在'我的文档'中")
print("要将它们显示在Base旁边，需要手动移动到同一文件夹")
print("=" * 60)
