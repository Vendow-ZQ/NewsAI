"""云文档存储抽象接口。

定义 DocStorage 基类，所有云文档后端（飞书 Docx、Notion 等）需实现此接口。
"""

from abc import ABC, abstractmethod
from typing import Optional


class DocStorage(ABC):
    """云文档存储抽象基类。

    支持创建文档、追加内容、获取分享链接、设置权限。
    """

    @abstractmethod
    def create_doc(self, title: str, folder_token: Optional[str] = None) -> str:
        """创建一份空白 Docx 文档。

        Args:
            title: 文档标题
            folder_token: 父文件夹 token，None 则创建在根目录

        Returns:
            document_id（飞书 docx ID，含 ldx 前缀或不含）
        """
        ...

    @abstractmethod
    def append_section(self, doc_id: str, markdown_content: str) -> None:
        """在文档末尾追加 markdown 内容。

        Args:
            doc_id: 文档 ID
            markdown_content: Markdown 格式文本
        """
        ...

    @abstractmethod
    def get_share_url(self, doc_id: str) -> str:
        """获取文档分享链接（含 https://.../docx/...）。

        Args:
            doc_id: 文档 ID

        Returns:
            可外部访问的 URL 字符串
        """
        ...

    @abstractmethod
    def set_permissions(self, doc_id: str, share_type: str = "tenant_editable") -> None:
        """设置文档权限。

        Args:
            doc_id: 文档 ID
            share_type: 分享类型
                - tenant_editable: 组织内可编辑（默认）
                - tenant_readable: 组织内仅查看
                - anyone_readable: 任何人可查看
        """
        ...
