"""
飞书Bitable适配器基础组件

包含：
- id_mapping: 业务ID与飞书record_id映射管理
- tables: 7张表的Schema定义和种子数据
"""

from .id_mapping import IDMapping
from .tables import (
    TABLES,
    get_table_fields,
    get_table_prefix,
    get_seed_data,
    # 字段类型常量
    FIELD_TYPE_TEXT,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_SINGLE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_URL,
    # 表字段定义
    SOURCE_CONFIG_FIELDS,
    TREND_FIELDS,
    TOPIC_FIELDS,
    DATA_FIELDS,
    KOC_FIELDS,
    EMP_FIELDS,
    LOG_FIELDS,
    # 种子数据
    SOURCE_CONFIG_SEED_DATA,
    KOC_SEED_DATA,
    EMP_SEED_DATA,
)

__all__ = [
    "IDMapping",
    "TABLES",
    "get_table_fields",
    "get_table_prefix",
    "get_seed_data",
    "FIELD_TYPE_TEXT",
    "FIELD_TYPE_NUMBER",
    "FIELD_TYPE_SINGLE_SELECT",
    "FIELD_TYPE_MULTI_SELECT",
    "FIELD_TYPE_DATETIME",
    "FIELD_TYPE_CHECKBOX",
    "FIELD_TYPE_URL",
    "SOURCE_CONFIG_FIELDS",
    "TREND_FIELDS",
    "TOPIC_FIELDS",
    "DATA_FIELDS",
    "KOC_FIELDS",
    "EMP_FIELDS",
    "LOG_FIELDS",
    "SOURCE_CONFIG_SEED_DATA",
    "KOC_SEED_DATA",
    "EMP_SEED_DATA",
]
