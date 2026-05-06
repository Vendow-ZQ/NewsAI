"""飞书云空间文件夹管理器。

负责创建并维护 NewsAI产物/ 根文件夹及 4 个子文件夹：
- 帖子
- 视频脚本
- 审改
- 经验
"""

import os
from typing import Optional, Dict

from lark_oapi import Client
from lark_oapi.api.drive.v1 import (
    CreateFolderFileRequest, CreateFolderFileRequestBuilder,
    CreateFolderFileRequestBody, CreateFolderFileRequestBodyBuilder,
    CreateFolderFileResponse,
    ListFileRequest, ListFileRequestBuilder,
)


class FolderManager:
    """飞书云空间文件夹管理器。"""

    ROOT_FOLDER_NAME = "NewsAI产物"
    SUB_FOLDERS = ["帖子", "视频脚本", "审改", "经验"]

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("LARK_APP_ID")
        self.app_secret = app_secret or os.getenv("LARK_APP_SECRET")
        if not all([self.app_id, self.app_secret]):
            raise ValueError("缺少飞书应用凭证")

        self.client = Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .build()

        self._folder_tokens: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 文件夹 CRUD
    # ------------------------------------------------------------------

    def create_folder(self, name: str, parent_token: Optional[str] = None) -> str:
        """创建文件夹，返回 folder_token。"""
        builder = CreateFolderFileRequestBodyBuilder().name(name)
        if parent_token:
            builder = builder.folder_token(parent_token)
        body = builder.build()

        req = CreateFolderFileRequest.builder() \
            .request_body(body) \
            .build()

        resp = self.client.drive.v1.file.create_folder(req)

        if not resp.success():
            # 应用可能没有 drive:drive 权限，抛出异常由上层处理
            raise Exception(f"创建文件夹失败: {resp.code} {resp.msg} (请检查应用是否开通 drive:drive 权限)")

        folder_token = resp.data.token
        return folder_token

    def list_root_folders(self) -> Dict[str, str]:
        """列出根目录下所有文件夹，返回 {name: token}。"""
        resp = self.client.drive.v1.file.list(
            ListFileRequest.builder()
                .page_size(200)
                .build()
        )
        if not resp.success():
            return {}

        result = {}
        for item in (resp.data.files or []):
            if getattr(item, "type", "") == "folder":
                result[getattr(item, "name", "")] = getattr(item, "token", "")
        return result

    # ------------------------------------------------------------------
    # NewsAI 专用初始化
    # ------------------------------------------------------------------

    def ensure_newsai_folders(self) -> Dict[str, str]:
        """确保 NewsAI产物 根文件夹及 4 个子文件夹存在。

        Returns:
            {
                "root": root_token,
                "帖子": posts_token,
                "视频脚本": scripts_token,
                "审改": audit_token,
                "经验": exp_token,
            }
        """
        # 1. 查找或创建根文件夹
        root_folders = self.list_root_folders()
        root_token = root_folders.get(self.ROOT_FOLDER_NAME)
        if not root_token:
            root_token = self.create_folder(self.ROOT_FOLDER_NAME)
            print(f"[FolderManager] 创建根文件夹: {self.ROOT_FOLDER_NAME}")
        else:
            print(f"[FolderManager] 根文件夹已存在: {self.ROOT_FOLDER_NAME}")

        self._folder_tokens["root"] = root_token

        # 2. 查找或创建子文件夹
        # 先列出根文件夹下的内容
        resp = self.client.drive.v1.file.list(
            ListFileRequest.builder()
                .folder_token(root_token)
                .page_size(200)
                .build()
        )
        existing_subs = {}
        if resp.success():
            for item in (resp.data.files or []):
                if getattr(item, "type", "") == "folder":
                    existing_subs[getattr(item, "name", "")] = getattr(item, "token", "")

        for sub_name in self.SUB_FOLDERS:
            token = existing_subs.get(sub_name)
            if not token:
                token = self.create_folder(sub_name, parent_token=root_token)
                print(f"[FolderManager] 创建子文件夹: {sub_name}")
            else:
                print(f"[FolderManager] 子文件夹已存在: {sub_name}")
            self._folder_tokens[sub_name] = token

        return dict(self._folder_tokens)

    def get_folder_token(self, name: str) -> Optional[str]:
        """获取已初始化文件夹的 token。"""
        return self._folder_tokens.get(name)
