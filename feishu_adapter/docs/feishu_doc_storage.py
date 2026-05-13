"""飞书云文档存储实现 —— DocStorage 接口。

基于 lark-oapi docx.v1 + drive.v1 实现：
- create_doc: 创建空白 Docx
- append_section: 追加 markdown 内容（通过 markdown_to_blocks 转换）
- get_share_url: 构造分享链接
- set_permissions: 设置公开/组织内权限
"""

import os
from typing import Optional, List

from lark_oapi import Client
from lark_oapi.api.docx.v1 import (
    CreateDocumentRequest, CreateDocumentRequestBuilder,
    CreateDocumentRequestBody, CreateDocumentRequestBodyBuilder,
    CreateDocumentBlockChildrenRequest, CreateDocumentBlockChildrenRequestBuilder,
    CreateDocumentBlockChildrenRequestBody, CreateDocumentBlockChildrenRequestBodyBuilder,
    ListDocumentBlockRequest, ListDocumentBlockRequestBuilder,
)
from lark_oapi.api.drive.v1 import (
    PatchPermissionPublicRequest, PatchPermissionPublicRequestBuilder,
)

from core.storage.doc_interface import DocStorage
from feishu_adapter.docs.markdown_to_blocks import markdown_to_blocks


class FeishuDocStorage(DocStorage):
    """飞书 Docx 云文档存储实现。"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("LARK_APP_ID")
        self.app_secret = app_secret or os.getenv("LARK_APP_SECRET")
        if not all([self.app_id, self.app_secret]):
            raise ValueError("缺少飞书应用凭证 LARK_APP_ID / LARK_APP_SECRET")

        self.client = Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .build()

    # ------------------------------------------------------------------
    # DocStorage 接口实现
    # ------------------------------------------------------------------

    def create_doc(self, title: str, folder_token: Optional[str] = None) -> str:
        """创建空白 Docx，返回 document_id。"""
        body_builder = CreateDocumentRequestBodyBuilder().title(title)
        if folder_token:
            body_builder = body_builder.folder_token(folder_token)

        resp = self.client.docx.v1.document.create(
            CreateDocumentRequest.builder()
                .request_body(body_builder.build())
                .build()
        )

        if not resp.success():
            raise Exception(f"创建文档失败: {resp.code} {resp.msg}")

        doc_id = resp.data.document.document_id
        return doc_id

    def append_section(self, doc_id: str, markdown_content: str) -> None:
        """在文档末尾追加 markdown 章节。"""
        blocks = markdown_to_blocks(markdown_content)
        if not blocks:
            return

        # 飞书单次最多写入 50 个 block（实测 50 OK，55+ 会报 99992402）
        batch_size = 50
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]
            resp = self.client.docx.v1.document_block_children.create(
                CreateDocumentBlockChildrenRequest.builder()
                    .document_id(doc_id)
                    .block_id(doc_id)          # 根 block_id = document_id
                    .request_body(
                        CreateDocumentBlockChildrenRequestBodyBuilder()
                            .children(batch)
                            .build()
                    )
                    .build()
            )
            if not resp.success():
                raise Exception(f"追加文档内容失败: {resp.code} {resp.msg}")

    def get_share_url(self, doc_id: str) -> str:
        """构造分享链接（飞书 Docx URL 固定格式）。"""
        # 飞书 Docx 分享链接格式（域名与租户绑定）
        return f"https://f5tgebopkn.feishu.cn/docx/{doc_id}"

    def read_doc_content(self, doc_id: str) -> str:
        """读取文档纯文本内容。

        Args:
            doc_id: 文档 ID

        Returns:
            文档纯文本内容
        """

        def _get_text_elements(block) -> list:
            """获取 block 的 Text 对象（含 elements 列表）。

            飞书 SDK 中不同 block_type 对应不同属性名：
            - type=2 (text)     -> block.text
            - type=3 (heading1) -> block.heading1
            - type=4 (heading2) -> block.heading2
            - type=5 (heading3) -> block.heading3
            - type=12 (bullet)  -> block.bullet
            - type=13 (ordered) -> block.ordered
            - type=15 (quote)   -> block.quote
            - type=22 (code)    -> block.code
            """
            bt = block.block_type
            attr_map = {
                2: "text",
                3: "heading1",
                4: "heading2",
                5: "heading3",
                12: "bullet",
                13: "ordered",
                15: "quote",
                22: "code",
            }
            attr_name = attr_map.get(bt)
            if not attr_name:
                return []
            text_obj = getattr(block, attr_name, None)
            if not text_obj:
                return []
            # code block 结构不同: block.code 直接是 Text，但其他 block 也是 Text
            if bt == 22 and hasattr(text_obj, "code_block"):
                # code block 的 elements 在 code_block 下
                cb = getattr(text_obj, "code_block", None)
                if cb and hasattr(cb, "elements"):
                    return cb.elements or []
                return []
            if hasattr(text_obj, "elements"):
                return text_obj.elements or []
            return []

        def _extract_text(elements: list) -> str:
            """从 TextElement 列表提取纯文本。

            关键修复：TextElement 没有 .text 属性，内容在 .text_run.content 中。
            """
            parts = []
            for elem in elements:
                # 优先取 text_run.content（最常用）
                tr = getattr(elem, "text_run", None)
                if tr:
                    content = getattr(tr, "content", "")
                    if content:
                        parts.append(content)
                    continue
                # 备用：text 属性（某些 SDK 版本可能有）
                t = getattr(elem, "text", None)
                if t:
                    content = getattr(t, "content", "")
                    if content:
                        parts.append(content)
            return "".join(parts)

        try:
            # 获取文档块列表
            resp = self.client.docx.v1.document_block.list(
                ListDocumentBlockRequest.builder()
                    .document_id(doc_id)
                    .page_size(500)
                    .build()
            )

            if not resp.success():
                return f"[读取文档失败: {resp.msg}]"

            if not resp.data or not resp.data.items:
                return ""

            # 提取文本内容
            texts = []
            for block in resp.data.items:
                try:
                    bt = block.block_type

                    # 跳过根 page 块 (type=1)，它的 children 只是 ID 列表
                    if bt == 1:
                        continue

                    elements = _get_text_elements(block)
                    text = _extract_text(elements)

                    if not text:
                        continue

                    # 根据类型加前缀
                    if bt == 3:
                        texts.append(f"# {text}")
                    elif bt == 4:
                        texts.append(f"## {text}")
                    elif bt == 5:
                        texts.append(f"### {text}")
                    elif bt == 12:
                        texts.append(f"- {text}")
                    elif bt == 13:
                        texts.append(f"1. {text}")
                    elif bt == 15:
                        texts.append(f"> {text}")
                    elif bt == 22:
                        texts.append(f"```\n{text}\n```")
                    else:
                        texts.append(text)
                except Exception:
                    # 跳过无法解析的 block
                    continue

            return "\n".join(texts)
        except Exception as e:
            return f"[读取文档异常: {e}]"

    def extract_doc_id_from_url(self, url: str) -> str:
        """从分享链接提取 doc_id。

        Args:
            url: 飞书文档分享链接，如 https://xxx.feishu.cn/docx/ABC123

        Returns:
            doc_id (如 ABC123)
        """
        if "/docx/" in url:
            return url.split("/docx/")[-1].split("?")[0]
        return url

    def set_permissions(self, doc_id: str, share_type: str = "tenant_editable") -> None:
        """设置文档权限（通过 HTTP 直接调用，SDK 封装不稳定）。

        Args:
            doc_id: 文档 ID
            share_type:
                - tenant_editable: 组织内可编辑
                - tenant_readable: 组织内仅查看
                - anyone_readable: 任何人可查看
        """
        import json
        import requests

        try:
            # 获取 tenant_access_token
            from lark_oapi.api.auth.v3 import (
                InternalTenantAccessTokenRequest,
                InternalTenantAccessTokenRequestBody,
            )
            token_resp = self.client.auth.v3.tenant_access_token.internal(
                InternalTenantAccessTokenRequest.builder()
                    .request_body(
                        InternalTenantAccessTokenRequestBody.builder()
                            .app_id(self.app_id)
                            .app_secret(self.app_secret)
                            .build()
                    )
                    .build()
            )
            if not token_resp.success():
                print("[警告] 获取 token 失败，跳过权限设置")
                return

            token_data = json.loads(token_resp.raw.content)
            tenant_token = token_data.get("tenant_access_token")

            url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{doc_id}/public"
            headers = {
                "Authorization": f"Bearer {tenant_token}",
                "Content-Type": "application/json",
            }

            # type is required
            if share_type == "anyone_readable":
                data = {
                    "type": "public",
                    "security_entity": "anyone_can_view",
                    "comment_entity": "anyone_can_view",
                    "share_entity": "anyone",
                    "link_share_entity": "anyone_readable",
                }
            else:  # tenant_readable
                data = {
                    "type": "public",
                    "security_entity": "only_full_access",
                    "comment_entity": "only_full_access",
                    "share_entity": "same_tenant",
                    "link_share_entity": "tenant_readable",
                }

            resp = requests.patch(url, headers=headers, json=data)
            result = resp.json()
            if result.get("code") != 0:
                print(f"[警告] 设置文档权限失败: {result.get('msg')}")
        except Exception as e:
            print(f"[警告] 权限设置异常: {e}")

    # ------------------------------------------------------------------
    # 便捷方法：按产物类型创建文档
    # ------------------------------------------------------------------

    def create_post_doc(self, topic_title: str, date_str: str, folder_token: str = None) -> str:
        """创建帖子文档：'[帖子] {date} {title}'"""
        title = f"[帖子] {date_str} {topic_title}"
        doc_id = self.create_doc(title, folder_token)
        return doc_id

    def create_script_doc(self, topic_title: str, date_str: str, folder_token: str = None) -> str:
        """创建脚本文档：'[脚本] {date} {title}'"""
        title = f"[脚本] {date_str} {topic_title}"
        doc_id = self.create_doc(title, folder_token)
        return doc_id

    def create_audit_doc(self, topic_title: str, date_str: str, folder_token: str = None) -> str:
        """创建审改文档：'[审改] {date} {title}'"""
        title = f"[审改] {date_str} {topic_title}"
        doc_id = self.create_doc(title, folder_token)
        return doc_id

    def create_experience_doc(self, period: str, theme: str, folder_token: str = None) -> str:
        """创建经验文档：'[经验] {period} {theme}'"""
        title = f"[经验] {period} {theme}"
        doc_id = self.create_doc(title, folder_token)
        return doc_id
