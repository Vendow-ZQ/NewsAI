#!/usr/bin/env python3
"""
飞书多维表格管理器
封装 lark-oapi SDK 和 HTTP API，提供简洁的表操作接口

Usage:
    from core.utils.feishu_base import FeishuBaseManager

    base = FeishuBaseManager(app_id, app_secret, base_token)

    # 创建表
    table_id = base.create_table("信息源配置", [{"name": "源名称", "type": 1}])

    # 写入记录
    record_id = base.create_record(table_id, {"源名称": "arXiv", "权重": 0.95})
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model.req_table import ReqTable
from lark_oapi.api.bitable.v1.model.app_table_create_header import AppTableCreateHeader
from lark_oapi.api.bitable.v1.model.patch_app_table_request import PatchAppTableRequest, PatchAppTableRequestBody
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody

# 加载环境变量
load_dotenv()


class FeishuBaseManager:
    """飞书多维表格管理器"""

    # 字段类型映射
    FIELD_TYPES = {
        "text": 1,      # 文本
        "number": 2,    # 数字
        "single_select": 3,  # 单选
        "multi_select": 4,   # 多选
        "datetime": 5,  # 日期时间
        "checkbox": 7,  # 复选框
        "user": 11,     # 人员
        "phone": 13,    # 电话
        "url": 15,      # 超链接
    }

    def __init__(self, app_id: str = None, app_secret: str = None, base_token: str = None):
        """
        初始化管理器

        Args:
            app_id: 飞书应用ID，默认从环境变量 LARK_APP_ID 读取
            app_secret: 飞书应用密钥，默认从环境变量 LARK_APP_SECRET 读取
            base_token: 多维表格ID，默认从环境变量 LARK_BASE_APP_TOKEN 读取
        """
        self.app_id = app_id or os.getenv("LARK_APP_ID")
        self.app_secret = app_secret or os.getenv("LARK_APP_SECRET")
        self.base_token = base_token or os.getenv("LARK_BASE_APP_TOKEN")

        if not all([self.app_id, self.app_secret, self.base_token]):
            raise ValueError("缺少必要的配置参数，请检查 .env 文件或传入参数")

        # 初始化 SDK Client
        self.client = Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .build()

        # Token 缓存
        self._tenant_token = None

        # 表结构缓存 {table_name: table_id}
        self._table_cache = {}

        # 字段缓存 {table_id: {field_name: field_id}}
        self._field_cache = {}

    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token（带缓存）"""
        if not self._tenant_token:
            resp = self.client.auth.v3.tenant_access_token.internal(
                InternalTenantAccessTokenRequest.builder()
                    .request_body(InternalTenantAccessTokenRequestBody.builder()
                        .app_id(self.app_id)
                        .app_secret(self.app_secret)
                        .build())
                    .build()
            )
            if resp.success():
                data = json.loads(resp.raw.content)
                self._tenant_token = data.get('tenant_access_token')
            else:
                raise Exception(f"获取 tenant_token 失败: {resp.msg}")

        return self._tenant_token

    def _http_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """
        HTTP 请求辅助函数

        Args:
            method: HTTP 方法 (GET/POST/PUT/PATCH/DELETE)
            endpoint: API 端点（如 /tables/xxx/fields）
            data: 请求体数据
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_token}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_tenant_token()}",
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                resp = requests.get(url, headers=headers)
            elif method == "POST":
                resp = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, json=data)
            elif method == "PATCH":
                resp = requests.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"不支持的方法: {method}")

            # 检查响应
            content_type = resp.headers.get('content-type', '')
            if 'application/json' in content_type:
                return resp.json()
            else:
                return {"code": -1, "msg": f"非JSON响应: {resp.text[:100]}"}

        except Exception as e:
            return {"code": -1, "msg": str(e)}

    # ==================== 表操作 ====================

    def list_tables(self, use_cache: bool = True) -> Dict[str, str]:
        """
        列出所有数据表

        Args:
            use_cache: 是否使用缓存

        Returns:
            {表名: 表ID}
        """
        if use_cache and self._table_cache:
            return self._table_cache

        resp = self.client.bitable.v1.app_table.list(
            ListAppTableRequest.builder().app_token(self.base_token).build()
        )

        if resp.success():
            tables = {t.name: t.table_id for t in resp.data.items}
            self._table_cache = tables
            return tables
        else:
            raise Exception(f"列出表失败: {resp.msg}")

    def create_table(self, name: str, fields: List[Dict[str, Any]]) -> str:
        """
        创建数据表

        Args:
            name: 表名
            fields: 字段列表 [{"name": "字段名", "type": 1}, ...]

        Returns:
            表ID
        """
        # 构建字段定义
        field_headers = []
        for field in fields:
            field_type = field.get("type", 1)
            if isinstance(field_type, str):
                field_type = self.FIELD_TYPES.get(field_type, 1)

            field_headers.append(
                AppTableCreateHeader.builder()
                    .field_name(field["name"])
                    .type(field_type)
                    .build()
            )

        resp = self.client.bitable.v1.app_table.create(
            CreateAppTableRequest.builder()
                .app_token(self.base_token)
                .request_body(CreateAppTableRequestBody.builder()
                    .table(
                        ReqTable.builder()
                            .name(name)
                            .fields(field_headers)
                            .build()
                    )
                    .build()
                )
                .build()
        )

        if resp.success():
            table_id = resp.data.table_id
            self._table_cache[name] = table_id
            return table_id
        else:
            raise Exception(f"创建表失败: {resp.msg}")

    def rename_table(self, table_id: str, new_name: str) -> bool:
        """
        重命名数据表

        Args:
            table_id: 表ID
            new_name: 新表名

        Returns:
            是否成功
        """
        resp = self.client.bitable.v1.app_table.patch(
            PatchAppTableRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .request_body(PatchAppTableRequestBody.builder().name(new_name).build())
                .build()
        )

        if resp.success():
            # 更新缓存
            old_name = None
            for name, tid in self._table_cache.items():
                if tid == table_id:
                    old_name = name
                    break
            if old_name:
                del self._table_cache[old_name]
                self._table_cache[new_name] = table_id
            return True
        else:
            raise Exception(f"重命名表失败: {resp.msg}")

    def delete_table(self, table_id: str) -> bool:
        """
        删除数据表

        Args:
            table_id: 表ID

        Returns:
            是否成功
        """
        resp = self.client.bitable.v1.app_table.delete(
            DeleteAppTableRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .build()
        )

        if resp.success():
            # 清除缓存
            self._table_cache = {k: v for k, v in self._table_cache.items() if v != table_id}
            return True
        else:
            raise Exception(f"删除表失败: {resp.msg}")

    def get_or_create_table(self, name: str, fields: List[Dict[str, Any]]) -> str:
        """
        获取或创建表（如果不存在则创建）

        Args:
            name: 表名
            fields: 字段列表

        Returns:
            表ID
        """
        try:
            tables = self.list_tables()
            if name in tables:
                return tables[name]
        except:
            pass

        return self.create_table(name, fields)

    # ==================== 字段操作 ====================

    def list_fields(self, table_id: str, use_cache: bool = True) -> Dict[str, str]:
        """
        列出表的所有字段

        Args:
            table_id: 表ID
            use_cache: 是否使用缓存

        Returns:
            {字段名: 字段ID}
        """
        if use_cache and table_id in self._field_cache:
            return self._field_cache[table_id]

        resp = self.client.bitable.v1.app_table_field.list(
            ListAppTableFieldRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .build()
        )

        if resp.success():
            fields = {f.field_name: f.field_id for f in resp.data.items}
            self._field_cache[table_id] = fields
            return fields
        else:
            raise Exception(f"列出字段失败: {resp.msg}")

    def add_field(self, table_id: str, field_name: str, field_type: Union[int, str] = 1) -> str:
        """
        添加字段（使用HTTP API，SDK不支持）

        Args:
            table_id: 表ID
            field_name: 字段名
            field_type: 字段类型（数字或字符串）

        Returns:
            字段ID
        """
        # 转换类型
        if isinstance(field_type, str):
            field_type = self.FIELD_TYPES.get(field_type, 1)

        result = self._http_request(
            "POST",
            f"/tables/{table_id}/fields",
            {"field_name": field_name, "type": field_type}
        )

        if result.get("code") == 0:
            field_id = result.get("data", {}).get("field", {}).get("field_id")
            # 更新缓存
            if table_id in self._field_cache:
                self._field_cache[table_id][field_name] = field_id
            return field_id
        else:
            # 如果字段已存在，尝试从缓存获取
            if "Duplicated" in result.get("msg", ""):
                fields = self.list_fields(table_id, use_cache=False)
                if field_name in fields:
                    return fields[field_name]
            raise Exception(f"添加字段失败: {result.get('msg')}")

    def ensure_fields(self, table_id: str, fields: List[Dict[str, Any]]):
        """
        确保字段存在（不存在则创建）

        Args:
            table_id: 表ID
            fields: 字段列表 [{"name": "xxx", "type": 1}, ...]
        """
        existing = self.list_fields(table_id)

        for field in fields:
            name = field["name"]
            if name not in existing:
                field_type = field.get("type", 1)
                self.add_field(table_id, name, field_type)
                print(f"[INFO] 添加字段: {name}")

    # ==================== 记录操作 ====================

    def create_record(self, table_id: str, fields: Dict[str, Any]) -> str:
        """
        创建记录

        Args:
            table_id: 表ID
            fields: 字段值字典 {字段名: 值}

        Returns:
            记录ID
        """
        resp = self.client.bitable.v1.app_table_record.create(
            CreateAppTableRecordRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .request_body({"fields": fields})
                .build()
        )

        if resp.success():
            return resp.data.record.record_id
        else:
            raise Exception(f"创建记录失败: {resp.msg}")

    def batch_create_records(self, table_id: str, records: List[Dict[str, Any]]) -> List[str]:
        """
        批量创建记录

        Args:
            table_id: 表ID
            records: 记录列表 [{"fields": {字段名: 值}}, ...]

        Returns:
            记录ID列表
        """
        resp = self.client.bitable.v1.app_table_record.batch_create(
            BatchCreateAppTableRecordRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build())
                .build()
        )

        if resp.success():
            return [r.record_id for r in resp.data.records]
        else:
            raise Exception(f"批量创建记录失败: {resp.msg}")

    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            table_id: 表ID
            record_id: 记录ID
            fields: 要更新的字段值

        Returns:
            是否成功
        """
        resp = self.client.bitable.v1.app_table_record.update(
            UpdateAppTableRecordRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .record_id(record_id)
                .request_body({"fields": fields})
                .build()
        )

        return resp.success()

    def get_record(self, table_id: str, record_id: str) -> Dict[str, Any]:
        """
        获取单条记录

        Args:
            table_id: 表ID
            record_id: 记录ID

        Returns:
            记录数据 {"record_id": "xxx", "fields": {...}}
        """
        resp = self.client.bitable.v1.app_table_record.get(
            GetAppTableRecordRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .record_id(record_id)
                .build()
        )

        if resp.success():
            return {
                "record_id": resp.data.record.record_id,
                "fields": resp.data.record.fields
            }
        else:
            raise Exception(f"获取记录失败: {resp.msg}")

    def list_records(self, table_id: str, page_size: int = 500) -> List[Dict[str, Any]]:
        """
        列出所有记录（自动分页）

        Args:
            table_id: 表ID
            page_size: 每页记录数

        Returns:
            记录列表 [{"record_id": "xxx", "fields": {...}}, ...]
        """
        all_records = []
        page_token = None

        while True:
            builder = ListAppTableRecordRequest.builder() \
                .app_token(self.base_token) \
                .table_id(table_id) \
                .page_size(page_size)

            if page_token:
                builder.page_token(page_token)

            resp = self.client.bitable.v1.app_table_record.list(builder.build())

            if resp.success():
                items = resp.data.items or []
                for item in items:
                    all_records.append({
                        "record_id": item.record_id,
                        "fields": item.fields
                    })

                if not resp.data.has_more:
                    break
                page_token = resp.data.page_token
            else:
                raise Exception(f"列出记录失败: {resp.msg}")

        return all_records

    def delete_record(self, table_id: str, record_id: str) -> bool:
        """
        删除记录

        Args:
            table_id: 表ID
            record_id: 记录ID

        Returns:
            是否成功
        """
        resp = self.client.bitable.v1.app_table_record.delete(
            DeleteAppTableRecordRequest.builder()
                .app_token(self.base_token)
                .table_id(table_id)
                .record_id(record_id)
                .build()
        )

        return resp.success()

    # ==================== 日期时间转换工具 ====================

    @staticmethod
    def convert_datetime_to_timestamp(value) -> int:
        """将各种日期时间格式转换为飞书Base要求的毫秒时间戳。

        支持的输入格式：
        - datetime对象
        - ISO格式字符串（如"2026-05-04T12:00:00"）
        - 已有的时间戳（直接返回）

        Args:
            value: 日期时间值

        Returns:
            毫秒时间戳（int）
        """
        from datetime import datetime

        if value is None:
            return int(datetime.now().timestamp() * 1000)

        # 如果已经是数字（时间戳），直接返回
        if isinstance(value, (int, float)):
            return int(value)

        # 如果是datetime对象
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)

        # 如果是字符串，尝试解析
        if isinstance(value, str):
            try:
                # 尝试ISO格式
                if 'T' in value:
                    # 处理带Z的UTC时间
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    dt = datetime.fromisoformat(value)
                    return int(dt.timestamp() * 1000)
                # 尝试常见格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return int(dt.timestamp() * 1000)
                    except:
                        continue
            except Exception as e:
                print(f"[警告] 日期解析失败 '{value}': {e}")

        # 默认返回当前时间
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def prepare_record_fields(fields: Dict[str, Any], datetime_fields: List[str] = None) -> Dict[str, Any]:
        """准备记录字段，自动转换日期时间字段。

        Args:
            fields: 原始字段值字典
            datetime_fields: 需要转换为时间戳的字段名列表

        Returns:
            转换后的字段值字典
        """
        if not datetime_fields:
            return fields

        result = {}
        for key, value in fields.items():
            if key in datetime_fields and value is not None:
                result[key] = FeishuBaseManager.convert_datetime_to_timestamp(value)
            else:
                result[key] = value
        return result

    def query_records(self, table_id: str, filter_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        简单查询记录（内存过滤，适合数据量小的场景）

        Args:
            table_id: 表ID
            filter_conditions: 过滤条件 {字段名: 值}

        Returns:
            匹配的记录列表
        """
        all_records = self.list_records(table_id)
        results = []

        for record in all_records:
            match = True
            for key, value in filter_conditions.items():
                if record["fields"].get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)

        return results


# ==================== 便捷函数 ====================

def get_base_manager() -> FeishuBaseManager:
    """从环境变量获取配置，创建管理器实例"""
    return FeishuBaseManager()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 测试代码
    print("[TEST] FeishuBaseManager 测试\n")

    try:
        # 初始化
        base = get_base_manager()
        print("[OK] 初始化成功")

        # 列出表
        tables = base.list_tables()
        print(f"[OK] 发现 {len(tables)} 个表: {list(tables.keys())}")

        # 使用第一个表测试
        if tables:
            table_id = list(tables.values())[0]
            table_name = list(tables.keys())[0]
            print(f"\n使用表 '{table_name}': {table_id}")

            # 列出字段
            fields = base.list_fields(table_id)
            print(f"[OK] 字段: {list(fields.keys())}")

            # 创建记录
            record_id = base.create_record(table_id, {
                "标题": "FeishuBaseManager 测试记录",
                "内容": "这是一条测试数据"
            })
            print(f"[OK] 创建记录: {record_id}")

            # 查询记录
            record = base.get_record(table_id, record_id)
            print(f"[OK] 查询记录: {record['fields'].get('标题')}")

            # 更新记录
            success = base.update_record(table_id, record_id, {"内容": "已更新内容"})
            print(f"[{'OK' if success else 'ERROR'}] 更新记录")

            # 删除记录
            success = base.delete_record(table_id, record_id)
            print(f"[{'OK' if success else 'ERROR'}] 删除记录")

        print("\n[DONE] 所有测试通过!")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
