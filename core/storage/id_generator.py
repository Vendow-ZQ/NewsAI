"""
业务ID生成器

格式：{表前缀}-{YYYYMMDD}-{NNN}
例：SRC-20260504-001
"""

from datetime import datetime
from typing import Optional


class IDGenerator:
    """业务ID生成器，格式：{表前缀}-{YYYYMMDD}-{NNN}"""

    _counters: dict[str, int] = {}

    @classmethod
    def generate(cls, table_prefix: str, date: Optional[datetime] = None) -> str:
        """
        生成业务ID

        Args:
            table_prefix: 表前缀，如 SRC, TREND, TOPIC 等
            date: 日期，默认为当前时间

        Returns:
            业务ID字符串，如 SRC-20260504-001
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y%m%d")
        key = f"{table_prefix}:{date_str}"

        if key not in cls._counters:
            cls._counters[key] = 0

        cls._counters[key] += 1
        return f"{table_prefix}-{date_str}-{cls._counters[key]:03d}"

    @classmethod
    def reset(cls, table_prefix: str = None, date: Optional[datetime] = None):
        """
        重置计数器（主要用于测试）

        Args:
            table_prefix: 指定表前缀，如不提供则重置所有
            date: 指定日期，默认为当前时间
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y%m%d")

        if table_prefix:
            key = f"{table_prefix}:{date_str}"
            if key in cls._counters:
                del cls._counters[key]
        else:
            # 重置所有计数器
            cls._counters.clear()


# 表前缀常量
TABLE_PREFIXES = {
    "信源配置": "SRC",
    "热帖库": "TREND",
    "选题库": "TOPIC",
    "内容资产库": "ASSET",
    "数据库": "DATA",
    "KOC人设": "KOC",
    "Agent花名册": "EMP",
    "Agent协作日志": "LOG",
}


def generate_id(table_name: str, date: Optional[datetime] = None) -> str:
    """
    根据表名生成业务ID

    Args:
        table_name: 中文表名，如 "信源配置", "热帖库" 等
        date: 日期，默认为当前时间

    Returns:
        业务ID字符串

    Raises:
        ValueError: 表名不存在时抛出
    """
    prefix = TABLE_PREFIXES.get(table_name)
    if not prefix:
        raise ValueError(f"未知的表名: {table_name}，支持的表名: {list(TABLE_PREFIXES.keys())}")

    return IDGenerator.generate(prefix, date)
