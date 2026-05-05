"""
飞书文档存储实现 - 向现有文档追加内容

管理4类内容产物的飞书文档（已预先创建好）：
1. 帖子内容文档 - 小文写入
2. 视频脚本文档 - 小播写入
3. 审改记录文档 - 小审/小改写入（累积追加）
4. 经验总结文档 - 小数写入

文档ID格式：ldx开头（飞书Docx）
"""

import os
from typing import Optional, List
from datetime import datetime

from lark_oapi import Client
from lark_oapi.api.docx.v1 import (
    CreateDocumentBlockChildrenRequest,
    CreateDocumentBlockChildrenRequestBodyBuilder,
    Block,
    BlockBuilder,
    TextBuilder,
    TextElementBuilder,
    TextRunBuilder,
)


class FeishuDocStorage:
    """飞书文档存储管理器 - 向现有文档追加内容"""

    # Block类型常量
    BLOCK_TEXT = 2          # 普通文本
    BLOCK_HEADING1 = 3      # 标题1
    BLOCK_HEADING2 = 4      # 标题2
    BLOCK_HEADING3 = 5      # 标题3
    BLOCK_BULLET = 12       # 无序列表
    BLOCK_NUMBERED = 13     # 有序列表
    BLOCK_CODE = 22         # 代码块

    # 预创建的文档ID（在Base旁边的4个文档）
    DOC_POSTS = "YF7KdiGRbok8PHx3RJOcWTq4nl9"      # 帖子内容
    DOC_SCRIPTS = "UuiJdk6vio6vgNx8GAncokuenje"    # 视频脚本
    DOC_AUDIT = "JYQLdwZM3o92Rrxt21jcIh2dnCV"      # 审改记录
    DOC_EXPERIENCE = "CnkQdzX9roUH2CxvkQzcCCXGn3e" # 经验总结

    def __init__(self, app_id: str = None, app_secret: str = None):
        """初始化文档存储"""
        self.app_id = app_id or os.getenv("LARK_APP_ID")
        self.app_secret = app_secret or os.getenv("LARK_APP_SECRET")

        if not all([self.app_id, self.app_secret]):
            raise ValueError("缺少飞书应用凭证")

        self.client = Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .build()

    def append_to_document(self, doc_id: str, content: str, block_type: int = 2):
        """
        向现有文档追加文本内容

        Args:
            doc_id: 文档ID
            content: 文本内容
            block_type: Block类型，默认2是普通文本
        """
        # 构造文本Block
        text_run = TextRunBuilder().content(content).build()
        element = TextElementBuilder().text_run(text_run).build()
        text = TextBuilder().elements([element]).build()

        builder = BlockBuilder().block_type(block_type)
        if block_type == self.BLOCK_TEXT:
            builder = builder.text(text)
        elif block_type == self.BLOCK_HEADING1:
            builder = builder.heading1(text)
        elif block_type == self.BLOCK_HEADING2:
            builder = builder.heading2(text)
        elif block_type == self.BLOCK_HEADING3:
            builder = builder.heading3(text)
        elif block_type == self.BLOCK_BULLET:
            builder = builder.bullet(text)
        elif block_type == self.BLOCK_CODE:
            builder = builder.code(text)
        else:
            builder = builder.text(text)

        block = builder.build()

        # 写入内容
        resp = self.client.docx.v1.document_block_children.create(
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
            raise Exception(f"写入文档内容失败: {resp.msg}")

    def append_markdown_to_doc(self, doc_id: str, markdown_content: str):
        """
        将Markdown内容追加到文档
        简单解析Markdown，转换为飞书Block
        """
        lines = markdown_content.split('\n')
        blocks = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析Markdown标题
            if line.startswith('# '):
                content = line[2:]
                block_type = self.BLOCK_HEADING1
            elif line.startswith('## '):
                content = line[3:]
                block_type = self.BLOCK_HEADING2
            elif line.startswith('### '):
                content = line[4:]
                block_type = self.BLOCK_HEADING3
            elif line.startswith('- ') or line.startswith('* '):
                content = line[2:]
                block_type = self.BLOCK_BULLET
            elif line.startswith('```'):
                # 代码块开始/结束，跳过
                continue
            else:
                content = line
                block_type = self.BLOCK_TEXT

            text_run = TextRunBuilder().content(content).build()
            element = TextElementBuilder().text_run(text_run).build()
            text = TextBuilder().elements([element]).build()

            builder = BlockBuilder().block_type(block_type)
            if block_type == self.BLOCK_TEXT:
                builder = builder.text(text)
            elif block_type == self.BLOCK_HEADING1:
                builder = builder.heading1(text)
            elif block_type == self.BLOCK_HEADING2:
                builder = builder.heading2(text)
            elif block_type == self.BLOCK_HEADING3:
                builder = builder.heading3(text)
            elif block_type == self.BLOCK_BULLET:
                builder = builder.bullet(text)

            blocks.append(builder.build())

        # 批量写入（每次最多100个block）
        batch_size = 100
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]

            resp = self.client.docx.v1.document_block_children.create(
                CreateDocumentBlockChildrenRequest.builder()
                    .document_id(doc_id)
                    .block_id(doc_id)
                    .request_body(
                        CreateDocumentBlockChildrenRequestBodyBuilder()
                            .children(batch)
                            .build()
                    )
                    .build()
            )

            if not resp.success():
                raise Exception(f"写入文档内容失败: {resp.msg}")

    def get_document_url(self, doc_id: str) -> str:
        """获取文档分享链接"""
        return f"https://jneyh7qlo8i.feishu.cn/docx/{doc_id}"

    # ============ 4类内容产物的便捷方法 ============

    def append_to_posts_doc(self, content: str):
        """向帖子内容文档追加内容"""
        self.append_to_document(self.DOC_POSTS, content)
        return self.get_document_url(self.DOC_POSTS)

    def append_to_scripts_doc(self, content: str):
        """向视频脚本文档追加内容"""
        self.append_to_document(self.DOC_SCRIPTS, content)
        return self.get_document_url(self.DOC_SCRIPTS)

    def append_to_audit_doc(self, content: str):
        """向审改记录文档追加内容"""
        self.append_to_document(self.DOC_AUDIT, content)
        return self.get_document_url(self.DOC_AUDIT)

    def append_to_experience_doc(self, content: str):
        """向经验总结文档追加内容"""
        self.append_to_document(self.DOC_EXPERIENCE, content)
        return self.get_document_url(self.DOC_EXPERIENCE)


# 便捷函数
def get_doc_storage() -> FeishuDocStorage:
    """获取文档存储实例（从环境变量）"""
    return FeishuDocStorage()
