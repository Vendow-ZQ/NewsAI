"""飞书文档 SDK Hello World 测试

验证 lark-oapi 的 docx API 能力：
1. 创建空白文档
2. 写入 markdown 风格内容（H1、H2、正文、列表、代码块）
3. 获取文档分享链接
4. 设置文档权限

结论：飞书文档 API 不支持直接写 markdown，需要通过 block 结构构造内容。
"""

import os
from dotenv import load_dotenv

from lark_oapi import Client
from lark_oapi.api.docx.v1 import (
    CreateDocumentRequest,
    CreateDocumentRequestBodyBuilder,
    CreateDocumentBlockChildrenRequest,
    CreateDocumentBlockChildrenRequestBodyBuilder,
    Block,
    BlockBuilder,
    TextBuilder,
    TextElementBuilder,
    TextRunBuilder,
)

# 加载环境变量
load_dotenv()

APP_ID = os.getenv("LARK_APP_ID")
APP_SECRET = os.getenv("LARK_APP_SECRET")


def build_client() -> Client:
    """构建飞书 SDK 客户端。"""
    return Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .build()


def make_text_block(content: str, block_type: int) -> Block:
    """构造一个文本类型的 Block。

    Args:
        content: 文本内容
        block_type: 块类型
            2=text, 3=heading1, 4=heading2, 12=bullet, 22=code_block
    """
    text_run = TextRunBuilder().content(content).build()
    element = TextElementBuilder().text_run(text_run).build()
    text = TextBuilder().elements([element]).build()

    builder = BlockBuilder().block_type(block_type)

    # 根据 block_type 设置对应的内容属性
    if block_type == 2:
        builder = builder.text(text)
    elif block_type == 3:
        builder = builder.heading1(text)
    elif block_type == 4:
        builder = builder.heading2(text)
    elif block_type == 12:
        builder = builder.bullet(text)
    elif block_type == 22:
        builder = builder.code(text)
    else:
        builder = builder.text(text)

    return builder.build()


def create_document(client: Client, title: str) -> str:
    """创建飞书文档，返回 document_id。"""
    resp = client.docx.v1.document.create(
        CreateDocumentRequest.builder()
            .request_body(
                CreateDocumentRequestBodyBuilder()
                    .title(title)
                    .build()
            )
            .build()
    )

    if resp.success():
        doc_id = resp.data.document.document_id
        print(f"[OK] 文档创建成功: {doc_id}")
        return doc_id
    else:
        raise Exception(f"创建文档失败: {resp.code} {resp.msg}")


def write_blocks(client: Client, document_id: str, blocks: list[Block]):
    """向文档写入一批 Block。

    注意：必须指定 block_id=document_id（文档根节点的 block_id 就是 document_id 本身），
    否则 API 返回 1770001 invalid param。
    """
    resp = client.docx.v1.document_block_children.create(
        CreateDocumentBlockChildrenRequest.builder()
            .document_id(document_id)
            .block_id(document_id)  # 根节点的 block_id = document_id
            .request_body(
                CreateDocumentBlockChildrenRequestBodyBuilder()
                    .children(blocks)
                    .build()
            )
            .build()
    )

    if resp.success():
        print(f"[OK] 写入 {len(blocks)} 个 block 成功")
    else:
        raise Exception(f"写入 block 失败: {resp.code} {resp.msg}")


def set_document_permission(client: Client, document_id: str):
    """设置文档权限为组织内可见（通过更新文档权限设置）。"""
    # 飞书文档权限通过 drive API 设置
    # 使用 HTTP 直接调用
    import requests
    import json

    # 获取 tenant token
    from lark_oapi.api.auth.v3 import (
        InternalTenantAccessTokenRequest,
        InternalTenantAccessTokenRequestBody,
    )
    token_resp = client.auth.v3.tenant_access_token.internal(
        InternalTenantAccessTokenRequest.builder()
            .request_body(
                InternalTenantAccessTokenRequestBody.builder()
                    .app_id(APP_ID)
                    .app_secret(APP_SECRET)
                    .build()
            )
            .build()
    )

    if not token_resp.success():
        print(f"[WARN] 获取 token 失败，跳过权限设置")
        return False

    token_data = json.loads(token_resp.raw.content)
    tenant_token = token_data.get('tenant_access_token')

    # 设置文档权限：组织内可见
    url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{document_id}/public"
    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json",
    }
    data = {
        "security_entity": "anyone_can_view",  # 任何人可查看
        "comment_entity": "anyone_can_view",
        "share_entity": "tenant_can_view",  # 组织内可见
        "link_share_entity": "tenant_readable",  # 组织内可读
    }

    resp = requests.patch(url, headers=headers, json=data)
    result = resp.json()

    if result.get("code") == 0:
        print("[OK] 文档权限设置为组织内可见")
        return True
    else:
        print(f"[WARN] 权限设置失败: {result.get('msg')} (code={result.get('code')})")
        return False


def main():
    print("=" * 60)
    print("飞书文档 SDK Hello World 测试")
    print("=" * 60)

    if not APP_ID or not APP_SECRET:
        print("[ERROR] 缺少 LARK_APP_ID 或 LARK_APP_SECRET，请检查 .env 文件")
        return

    client = build_client()
    print(f"[OK] 客户端初始化成功 (app_id={APP_ID[:10]}...)")

    # 1. 创建文档
    print("\n--- 步骤 1: 创建文档 ---")
    document_id = create_document(client, "[NewsAI 测试] hello world")

    # 2. 构造 markdown 风格内容
    print("\n--- 步骤 2: 构造 Block 内容 ---")
    blocks = [
        # H1 标题
        make_text_block("NewsAI 飞书文档测试", 3),
        # H2 副标题
        make_text_block("这是一个技术验证文档", 4),
        # 正文段落
        make_text_block(
            "飞书文档 API 支持通过 Block 结构写入丰富的文档内容。"
            "每个 Block 都有类型（heading1、heading2、text、bullet、code 等），"
            "可以组合成完整的文档。",
            2,
        ),
        # H2: 功能列表
        make_text_block("支持的功能", 4),
        # 无序列表
        make_text_block("创建空白文档", 12),
        make_text_block("写入 H1/H2 标题", 12),
        make_text_block("写入正文段落", 12),
        make_text_block("写入无序列表", 12),
        make_text_block("写入代码块", 12),
        # H2: 代码示例
        make_text_block("代码示例", 4),
        # 代码块（注：code block type=22 当前 API 有兼容性问题，暂用 text block 替代）
        make_text_block("    print('Hello, Feishu Doc!')", 2),
    ]
    print(f"[OK] 构造了 {len(blocks)} 个 block")

    # 3. 写入文档
    print("\n--- 步骤 3: 写入文档 ---")
    write_blocks(client, document_id, blocks)

    # 4. 设置权限
    print("\n--- 步骤 4: 设置权限 ---")
    set_document_permission(client, document_id)

    # 5. 生成分享链接
    print("\n--- 步骤 5: 分享链接 ---")
    # 飞书文档链接格式
    share_url = f"https://f5tgebopkn.feishu.cn/docx/{document_id}"
    print(f"[OK] 文档分享链接: {share_url}")
    print(f"     (请在浏览器中打开验证)")

    print("\n" + "=" * 60)
    print("测试完成！")
    print(f"文档 ID: {document_id}")
    print(f"分享链接: {share_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
