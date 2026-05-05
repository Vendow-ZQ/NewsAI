"""
Storage 抽象层 - 统一存储接口

提供 create / update / query / delete 四个核心操作，
由 FeishuStorage 和 LocalStorage 分别实现。
"""

from .interface import Storage, StorageRecord, QueryFilter, StorageError, RecordNotFoundError, DuplicateRecordError
from .id_generator import IDGenerator, generate_id, TABLE_PREFIXES

__all__ = [
    "Storage", "StorageRecord", "QueryFilter",
    "StorageError", "RecordNotFoundError", "DuplicateRecordError",
    "IDGenerator", "generate_id", "TABLE_PREFIXES",
]
