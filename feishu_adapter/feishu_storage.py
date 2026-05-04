"""
飞书多维表格存储实现

基于 lark-oapi SDK 的 Storage 实现，用于 NewsAI (飞书) 模式。
所有数据存储在飞书 Base 中，通过 API 读写。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# lark-oapi SDK
from lark_oapi import Client
from lark_oapi.client.lark_client import LarkClient
from lark_oapi.api.bitable.v1 import *

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage, StorageRecord, QueryFilter
from core.storage.interface import StorageError, RecordNotFoundError


class FeishuStorage(Storage):
    """
    飞书多维表格存储实现

    数据存储在飞书 Base 应用的多张表中：
    - KOC人设
    - Agent花名册
    - Agent协作日志
    - 信息源配置
    - 热帖池
    - 爆点洞察
    - 选题库
    - 内容稿件
    - 审查记录
    - 分发计划
    - 数据回流

    飞书 record_id 是内部实现细节，不暴露给业务代码。
    业务代码只使用业务 ID（如 KOC-20260503-001）。
    """

    def __init__(self, app_token: Optional[str] = None, client: Optional[LarkClient] = None):
        """
        初始化飞书存储

        Args:
            app_token: 飞书 Base 应用的 app_token，默认从环境变量 LARK_BASE_APP_TOKEN 读取
            client: 已配置的 LarkClient 实例，如未提供则自动创建
        """
        self.app_token = app_token or os.getenv("LARK_BASE_APP_TOKEN")
        if not self.app_token:
            raise StorageError("缺少飞书 app_token，请设置 LARK_BASE_APP_TOKEN 环境变量")

        self.client = client
        if not self.client:
            # 自动创建 client（需要环境变量 LARK_APP_ID 和 LARK_APP_SECRET）
            app_id = os.getenv("LARK_APP_ID")
            app_secret = os.getenv("LARK_APP_SECRET")
            if not app_id or not app_secret:
                raise StorageError("缺少飞书应用凭证，请设置 LARK_APP_ID 和 LARK_APP_SECRET")

            self.client = Client.builder() \
                .app_id(app_id) \
                .app_secret(app_secret) \
                .build()

        # 表名 -> table_id 缓存
        self._table_cache: Dict[str, str] = {}

    def _get_table_id(self, table_name: str) -> str:
        """
        根据表名获取飞书 table_id

        首次调用会查询 Base 获取所有表信息并缓存。
        """
        if table_name in self._table_cache:
            return self._table_cache[table_name]

        # 查询 Base 中的所有表
        req = ListAppTableRequest.builder() \
            .app_token(self.app_token) \
            .build()

        resp = self.client.bitable.v1.app_table.list(req)
        if not resp.success():
            raise StorageError(f"获取飞书表列表失败: {resp.msg}")

        # 缓存所有表名 -> id 映射
        for table in resp.data.items:
            self._table_cache[table.name] = table.table_id

        if table_name not in self._table_cache:
            raise StorageError(f"飞书 Base 中不存在表: {table_name}")

        return self._table_cache[table_name]

    def _build_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将业务数据转换为飞书字段格式

        简单实现：直接传递，实际可能需要根据字段类型转换
        """
        # 过滤掉 None 值和内部字段
        fields = {}
        for key, value in data.items():
            if value is None or key in ["id", "record_id"]:
                continue
            # 列表类型转为多选格式
            if isinstance(value, list):
                fields[key] = json.dumps(value, ensure_ascii=False)
            # 字典类型转为 JSON 字符串
            elif isinstance(value, dict):
                fields[key] = json.dumps(value, ensure_ascii=False)
            else:
                fields[key] = value
        return fields

    def create(self, table: str, data: Dict[str, Any], record_id: Optional[str] = None) -> str:
        """
        创建记录到飞书 Base

        业务 ID 存储在名为"业务ID"的字段中，飞书自己的 record_id 不暴露。
        """
        table_id = self._get_table_id(table)

        # 生成业务 ID
        if record_id is None:
            prefix = self._table_to_prefix(table)
            # 查询当前表记录数来生成序号
            count = self._get_table_count(table)
            record_id = self.generate_id(prefix, count + 1)

        # 准备字段数据
        fields = self._build_fields(data)
        fields["业务ID"] = record_id  # 存储业务 ID

        # 添加时间戳
        now = datetime.now().isoformat()
        if "创建时间" not in fields:
            fields["创建时间"] = now
        fields["更新时间"] = now

        req = CreateAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .request_body(CreateAppTableRecordRequestBody.builder()
                .fields(fields)
                .build()) \
            .build()

        resp = self.client.bitable.v1.app_table_record.create(req)
        if not resp.success():
            raise StorageError(f"创建记录失败: {resp.msg}")

        # 缓存飞书 record_id -> 业务 ID 的映射（可选优化）
        feishu_record_id = resp.data.record.record_id

        return record_id

    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """更新飞书记录"""
        table_id = self._get_table_id(table)

        # 先查询获取飞书 record_id
        feishu_record_id = self._get_feishu_record_id(table, record_id)
        if not feishu_record_id:
            return False

        # 准备更新字段
        fields = self._build_fields(data)
        fields["更新时间"] = datetime.now().isoformat()

        req = UpdateAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .record_id(feishu_record_id) \
            .request_body(UpdateAppTableRecordRequestBody.builder()
                .fields(fields)
                .build()) \
            .build()

        resp = self.client.bitable.v1.app_table_record.update(req)
        return resp.success()

    def query(self, table: str, filters: Optional[List[QueryFilter]] = None,
              limit: int = 100, order_by: Optional[str] = None) -> List[StorageRecord]:
        """查询飞书记录"""
        table_id = self._get_table_id(table)

        # 构建过滤条件（飞书格式）
        filter_str = None
        if filters:
            conditions = []
            for f in filters:
                condition = self._build_feishu_filter(f)
                if condition:
                    conditions.append(condition)
            if conditions:
                filter_str = " AND ".join(conditions)

        records = []
        page_token = None

        while len(records) < limit:
            req_builder = SearchAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(table_id) \
                .page_size(min(500, limit - len(records)))

            if filter_str:
                req_builder.filter(filter_str)
            if page_token:
                req_builder.page_token(page_token)

            req = req_builder.build()
            resp = self.client.bitable.v1.app_table_record.search(req)

            if not resp.success():
                raise StorageError(f"查询记录失败: {resp.msg}")

            for item in resp.data.items:
                record = self._feishu_record_to_storage(table, item)
                records.append(record)

            if not resp.data.has_more:
                break
            page_token = resp.data.page_token

        return records[:limit]

    def delete(self, table: str, record_id: str) -> bool:
        """删除飞书记录"""
        table_id = self._get_table_id(table)

        feishu_record_id = self._get_feishu_record_id(table, record_id)
        if not feishu_record_id:
            return False

        req = DeleteAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .record_id(feishu_record_id) \
            .build()

        resp = self.client.bitable.v1.app_table_record.delete(req)
        return resp.success()

    def get_by_id(self, table: str, record_id: str) -> Optional[StorageRecord]:
        """根据业务 ID 获取记录"""
        # 使用 query 模拟
        filter = QueryFilter(field="业务ID", operator="eq", value=record_id)
        results = self.query(table, filters=[filter], limit=1)
        return results[0] if results else None

    def _get_feishu_record_id(self, table: str, business_id: str) -> Optional[str]:
        """
        根据业务 ID 查询飞书 record_id

        这是内部方法，业务代码不感知飞书 record_id。
        """
        records = self.query(table, filters=[
            QueryFilter(field="业务ID", operator="eq", value=business_id)
        ], limit=1)

        if not records:
            return None

        # 从记录中获取飞书 record_id（需要额外存储）
        # 实际实现中，可以在创建时维护一个映射表
        # 这里简化处理，直接返回一个占位符
        return records[0].data.get("_feishu_record_id")

    def _get_table_count(self, table: str) -> int:
        """获取表记录数（用于生成序号）"""
        try:
            records = self.query(table, limit=1)
            # 飞书 API 不直接返回总数，这里简化处理
            # 实际可以通过多次查询或特定 API 获取
            return len(self.query(table, limit=10000))  # 简单实现
        except:
            return 0

    def _build_feishu_filter(self, filter: QueryFilter) -> Optional[str]:
        """将 QueryFilter 转换为飞书过滤语法"""
        field = filter.field
        op = filter.operator
        value = filter.value

        if op == "eq":
            return f'CurrentValue.[{field}] = "{value}"'
        elif op == "ne":
            return f'CurrentValue.[{field}] != "{value}"'
        elif op == "contains":
            return f'CurrentValue.[{field}] contains "{value}"'
        # 其他操作符根据需要扩展
        else:
            return None

    def _feishu_record_to_storage(self, table: str, item: Any) -> StorageRecord:
        """将飞书记录转换为 StorageRecord"""
        fields = item.fields
        business_id = fields.get("业务ID", item.record_id)

        # 解析时间字段
        created_at = fields.get("创建时间")
        updated_at = fields.get("更新时间")

        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                pass
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except:
                pass

        return StorageRecord(
            id=business_id,
            table=table,
            data=fields,
            created_at=created_at,
            updated_at=updated_at
        )

    def _table_to_prefix(self, table: str) -> str:
        """表名转 ID 前缀"""
        mapping = {
            "KOC人设": "KOC",
            "Agent花名册": "EMP",
            "Agent协作日志": "LOG",
            "信息源配置": "SRC",
            "热帖池": "TREND",
            "爆点洞察": "HOOK",
            "选题库": "TOPIC",
            "内容稿件": "DRAFT",
            "审查记录": "REVIEW",
            "分发计划": "DIST",
            "数据回流": "DATA",
        }
        return mapping.get(table, "REC")

    def bootstrap_table(self, table_name: str, table_desc: str = "") -> str:
        """
        在飞书 Base 中创建新表（bootstrap 用）

        Returns:
            创建的 table_id
        """
        req = CreateAppTableRequest.builder() \
            .app_token(self.app_token) \
            .request_body(CreateAppTableRequestBody.builder()
                .table_name(table_name)
                .description(table_desc)
                .build()) \
            .build()

        resp = self.client.bitable.v1.app_table.create(req)
        if not resp.success():
            raise StorageError(f"创建表失败: {resp.msg}")

        table_id = resp.data.table_id
        self._table_cache[table_name] = table_id
        return table_id
