"""
飞书Bitable存储实现

基于FeishuBaseManager的Storage接口实现。
所有业务代码使用业务ID，内部通过IDMapping维护与飞书record_id的映射。
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage.interface import Storage, StorageRecord, QueryFilter
from core.storage.interface import StorageError, RecordNotFoundError
from core.storage.id_generator import IDGenerator, TABLE_PREFIXES
from core.utils.feishu_base import FeishuBaseManager
from feishu_adapter.base.id_mapping import IDMapping


class FeishuStorage(Storage):
    """
    飞书Bitable存储实现

    数据存储在飞书Base中，通过FeishuBaseManager操作。
    业务ID格式: {PREFIX}-{YYYYMMDD}-{NNN}
    内部通过IDMapping维护 business_id <-> record_id 映射。
    """

    def __init__(self, app_token: Optional[str] = None,
                 mapping_file: str = ".id_mapping.json"):
        """
        初始化飞书存储

        Args:
            app_token: 飞书Base的app_token，默认从环境变量读取
            mapping_file: ID映射文件路径
        """
        # 初始化FeishuBaseManager
        try:
            self.base = FeishuBaseManager(base_token=app_token)
        except ValueError as e:
            raise StorageError(f"初始化FeishuBaseManager失败: {e}")

        # 初始化ID映射
        self.id_mapping = IDMapping(mapping_file)

        # 表名 -> table_id 缓存
        self._table_cache: Dict[str, str] = {}

    def _get_table_id(self, table: str) -> str:
        """
        根据表名获取飞书table_id

        首次调用会查询Base获取所有表信息并缓存。
        """
        if table in self._table_cache:
            return self._table_cache[table]

        try:
            tables = self.base.list_tables()
            if table not in tables:
                raise StorageError(f"飞书Base中不存在表: {table}")

            self._table_cache[table] = tables[table]
            return tables[table]
        except Exception as e:
            raise StorageError(f"获取表ID失败: {e}")

    def _get_prefix(self, table: str) -> str:
        """根据表名获取ID前缀"""
        prefix = TABLE_PREFIXES.get(table)
        if not prefix:
            raise StorageError(f"未知的表名，无法确定ID前缀: {table}")
        return prefix

    def create(self, table: str, data: Dict[str, Any], record_id: Optional[str] = None) -> str:
        """
        创建记录

        Args:
            table: 表名（中文）
            data: 记录数据
            record_id: 可选的业务ID，如未提供则自动生成

        Returns:
            业务ID
        """
        # 确保表存在
        try:
            table_id = self._get_table_id(table)
        except StorageError:
            # 表不存在，尝试创建
            table_id = self._ensure_table_exists_simple(table)

        # 生成或使用提供的业务ID
        if record_id is None:
            prefix = self._get_prefix(table)
            record_id = IDGenerator.generate(prefix)

        # 准备字段数据
        fields = dict(data)
        fields["id"] = record_id

        # 添加时间戳（转换为飞书Base要求的毫秒时间戳）
        now_ms = FeishuBaseManager.convert_datetime_to_timestamp(datetime.now())
        if "创建时间" in [f.get("name") for f in self._get_table_fields(table_id)]:
            if "创建时间" not in fields:
                fields["创建时间"] = now_ms
        if "更新时间" in [f.get("name") for f in self._get_table_fields(table_id)]:
            fields["更新时间"] = now_ms

        try:
            # 创建记录
            feishu_record_id = self.base.create_record(table_id, fields)

            # 保存映射关系
            self.id_mapping.add(table, record_id, feishu_record_id)

            return record_id
        except Exception as e:
            raise StorageError(f"创建记录失败: {e}")

    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            table: 表名
            record_id: 业务ID
            data: 要更新的字段

        Returns:
            是否更新成功
        """
        table_id = self._get_table_id(table)

        # 获取飞书record_id
        feishu_record_id = self.id_mapping.get_record_id(table, record_id)
        if not feishu_record_id:
            # 尝试从飞书查询
            feishu_record_id = self._query_record_id_by_business_id(table, record_id)
            if not feishu_record_id:
                raise RecordNotFoundError(f"记录不存在: {record_id}")
            # 缓存映射
            self.id_mapping.add(table, record_id, feishu_record_id)

        # 准备更新字段
        fields = dict(data)
        if "更新时间" in [f.get("name") for f in self._get_table_fields(table_id)]:
            fields["更新时间"] = FeishuBaseManager.convert_datetime_to_timestamp(datetime.now())

        try:
            return self.base.update_record(table_id, feishu_record_id, fields)
        except Exception as e:
            raise StorageError(f"更新记录失败: {e}")

    def query(self, table: str, filters: Optional[List[QueryFilter]] = None,
              limit: int = 100, order_by: Optional[str] = None) -> List[StorageRecord]:
        """
        查询记录

        Args:
            table: 表名
            filters: 过滤条件列表
            limit: 返回记录数上限
            order_by: 排序字段

        Returns:
            StorageRecord列表
        """
        table_id = self._get_table_id(table)

        try:
            # 获取所有记录
            all_records = self.base.list_records(table_id)

            # 转换为StorageRecord
            results = []
            for record in all_records:
                storage_record = self._convert_to_storage_record(table, record)
                results.append(storage_record)

            # 应用过滤条件
            if filters:
                results = self._apply_filters(results, filters)

            # 应用排序
            if order_by:
                results = self._apply_ordering(results, order_by)

            return results[:limit]
        except Exception as e:
            raise StorageError(f"查询记录失败: {e}")

    def delete(self, table: str, record_id: str) -> bool:
        """
        删除记录

        Args:
            table: 表名
            record_id: 业务ID

        Returns:
            是否删除成功
        """
        table_id = self._get_table_id(table)

        # 获取飞书record_id
        feishu_record_id = self.id_mapping.get_record_id(table, record_id)
        if not feishu_record_id:
            feishu_record_id = self._query_record_id_by_business_id(table, record_id)
            if not feishu_record_id:
                return False

        try:
            success = self.base.delete_record(table_id, feishu_record_id)
            if success:
                self.id_mapping.remove(table, record_id)
            return success
        except Exception as e:
            raise StorageError(f"删除记录失败: {e}")

    def get_by_id(self, table: str, record_id: str) -> Optional[StorageRecord]:
        """
        根据业务ID获取单条记录

        Args:
            table: 表名
            record_id: 业务ID

        Returns:
            StorageRecord或None
        """
        table_id = self._get_table_id(table)

        # 获取飞书record_id
        feishu_record_id = self.id_mapping.get_record_id(table, record_id)
        if not feishu_record_id:
            feishu_record_id = self._query_record_id_by_business_id(table, record_id)
            if not feishu_record_id:
                return None
            self.id_mapping.add(table, record_id, feishu_record_id)

        try:
            record = self.base.get_record(table_id, feishu_record_id)
            return self._convert_to_storage_record(table, record)
        except Exception as e:
            raise StorageError(f"获取记录失败: {e}")

    def _query_record_id_by_business_id(self, table: str, business_id: str) -> Optional[str]:
        """
        通过业务ID查询飞书record_id

        当映射不存在时，通过查询飞书获取。
        """
        table_id = self._get_table_id(table)

        try:
            # 列出所有记录，查找匹配的business_id
            records = self.base.list_records(table_id)
            for record in records:
                fields = record.get("fields", {})
                if fields.get("id") == business_id:
                    return record.get("record_id")
            return None
        except Exception:
            return None

    def _convert_to_storage_record(self, table: str, record: Dict[str, Any]) -> StorageRecord:
        """将飞书记录转换为StorageRecord"""
        fields = record.get("fields", {})
        business_id = fields.get("id", record.get("record_id"))

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
            created_at=created_at if isinstance(created_at, datetime) else None,
            updated_at=updated_at if isinstance(updated_at, datetime) else None
        )

    def _apply_filters(self, records: List[StorageRecord],
                       filters: List[QueryFilter]) -> List[StorageRecord]:
        """应用过滤条件"""
        results = records
        for f in filters:
            results = [r for r in results if self._match_filter(r, f)]
        return results

    def _match_filter(self, record: StorageRecord, filter: QueryFilter) -> bool:
        """检查记录是否匹配过滤条件"""
        field_value = record.data.get(filter.field)

        if filter.operator == "eq":
            return field_value == filter.value
        elif filter.operator == "ne":
            return field_value != filter.value
        elif filter.operator == "contains":
            if isinstance(field_value, str) and isinstance(filter.value, str):
                return filter.value in field_value
            return False
        elif filter.operator == "gt":
            return field_value is not None and field_value > filter.value
        elif filter.operator == "gte":
            return field_value is not None and field_value >= filter.value
        elif filter.operator == "lt":
            return field_value is not None and field_value < filter.value
        elif filter.operator == "lte":
            return field_value is not None and field_value <= filter.value
        elif filter.operator == "in":
            return field_value in filter.value if isinstance(filter.value, (list, tuple)) else False
        return True

    def _apply_ordering(self, records: List[StorageRecord], order_by: str) -> List[StorageRecord]:
        """应用排序"""
        reverse = False
        if order_by.startswith("-"):
            reverse = True
            order_by = order_by[1:]

        return sorted(records, key=lambda r: r.data.get(order_by) or "", reverse=reverse)

    def _get_table_fields(self, table_id: str) -> List[Dict[str, Any]]:
        """获取表的字段定义"""
        try:
            fields = self.base.list_fields(table_id)
            return [{"name": name, "field_id": fid} for name, fid in fields.items()]
        except:
            return []

    def bootstrap_table(self, table_name: str, fields: List[Dict[str, Any]]) -> str:
        """
        在飞书Base中创建新表（bootstrap用）

        Args:
            table_name: 表名
            fields: 字段定义列表

        Returns:
            创建的table_id
        """
        try:
            table_id = self.base.create_table(table_name, fields)
            self._table_cache[table_name] = table_id
            return table_id
        except Exception as e:
            raise StorageError(f"创建表失败: {e}")

    def ensure_table_exists(self, table_name: str, fields: List[Dict[str, Any]]) -> str:
        """
        确保表存在（不存在则创建）

        Args:
            table_name: 表名
            fields: 字段定义列表

        Returns:
            table_id
        """
        try:
            tables = self.base.list_tables()
            if table_name in tables:
                return tables[table_name]
        except:
            pass

        return self.bootstrap_table(table_name, fields)

    def _ensure_table_exists_simple(self, table_name: str) -> str:
        """
        简化版确保表存在（使用默认字段）
        """
        # 默认字段配置
        default_fields = [
            {"name": "id", "type": "Text", "description": "业务ID"},
            {"name": "创建时间", "type": "DateTime", "description": "创建时间"},
            {"name": "更新时间", "type": "DateTime", "description": "更新时间"},
        ]

        # Agent协作日志表的特殊字段
        if table_name == "Agent协作日志":
            default_fields.extend([
                {"name": "AgentID", "type": "Text", "description": "Agent ID"},
                {"name": "Agent花名", "type": "Text", "description": "Agent名称"},
                {"name": "任务类型", "type": "Text", "description": "任务类型"},
                {"name": "输入摘要", "type": "Text", "description": "输入摘要"},
                {"name": "输出摘要", "type": "Text", "description": "输出摘要"},
                {"name": "执行状态", "type": "Text", "description": "执行状态"},
                {"name": "执行时间", "type": "Number", "description": "执行时间戳"},
            ])

        try:
            tables = self.base.list_tables()
            if table_name in tables:
                return tables[table_name]
        except:
            pass

        return self.bootstrap_table(table_name, default_fields)
