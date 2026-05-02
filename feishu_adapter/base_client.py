"""飞书多维表格 SDK 封装。"""

import os

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


def _build_client() -> lark.Client:
    """构建飞书 SDK 客户端。"""
    return lark.Client.builder() \
        .app_id(os.getenv("LARK_APP_ID", "")) \
        .app_secret(os.getenv("LARK_APP_SECRET", "")) \
        .build()


class FeishuBaseClient:
    """飞书多维表格 CRUD 封装。"""

    def __init__(self):
        self.client = _build_client()
        self.app_token = os.getenv("LARK_BASE_APP_TOKEN", "")

    async def create_record(self, table_id: str, fields: dict) -> dict:
        """创建一条记录。"""
        # TODO: lark-oapi create record
        raise NotImplementedError

    async def update_record(self, table_id: str, record_id: str, fields: dict) -> dict:
        """更新一条记录。"""
        # TODO: lark-oapi update record
        raise NotImplementedError

    async def query_records(self, table_id: str, filter_expr: str = "") -> list[dict]:
        """查询记录列表。"""
        # TODO: lark-oapi search records
        raise NotImplementedError

    async def batch_create_records(self, table_id: str, records: list[dict]) -> list[dict]:
        """批量创建记录。"""
        # TODO: lark-oapi batch create
        raise NotImplementedError
