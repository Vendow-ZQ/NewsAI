"""
Storage 抽象基类

定义统一的存储接口，所有存储实现必须继承此类。
业务代码通过依赖注入接收 Storage 实例，不感知底层实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StorageRecord:
    """存储记录的标准封装"""
    id: str
    table: str
    data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class QueryFilter:
    """查询条件封装"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, in
    value: Any


class Storage(ABC):
    """
    存储抽象基类

    所有存储实现（FeishuStorage, LocalStorage）必须实现这四个方法。
    业务 ID 格式: {PREFIX}-{YYYYMMDD}-{NNN}
    """

    @abstractmethod
    def create(self, table: str, data: Dict[str, Any], record_id: Optional[str] = None) -> str:
        """
        创建记录

        Args:
            table: 表名
            data: 记录数据字典
            record_id: 可选的业务 ID，如未提供则自动生成

        Returns:
            业务 ID (record_id)

        Raises:
            StorageError: 创建失败时抛出
        """
        pass

    @abstractmethod
    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            table: 表名
            record_id: 业务 ID
            data: 要更新的字段

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
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
            StorageRecord 列表
        """
        pass

    @abstractmethod
    def delete(self, table: str, record_id: str) -> bool:
        """
        删除记录

        Args:
            table: 表名
            record_id: 业务 ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def get_by_id(self, table: str, record_id: str) -> Optional[StorageRecord]:
        """
        根据 ID 获取单条记录

        Args:
            table: 表名
            record_id: 业务 ID

        Returns:
            StorageRecord 或 None
        """
        pass

    def exists(self, table: str, record_id: str) -> bool:
        """
        检查记录是否存在

        默认实现基于 get_by_id，子类可覆盖优化。
        """
        return self.get_by_id(table, record_id) is not None

    def generate_id(self, prefix: str, sequence_num: int) -> str:
        """
        生成业务 ID

        格式: {PREFIX}-{YYYYMMDD}-{NNN}
        例: KOC-20260503-001
        """
        today = datetime.now().strftime("%Y%m%d")
        return f"{prefix}-{today}-{sequence_num:03d}"


class StorageError(Exception):
    """存储操作异常基类"""
    pass


class RecordNotFoundError(StorageError):
    """记录不存在异常"""
    pass


class DuplicateRecordError(StorageError):
    """记录重复异常"""
    pass
