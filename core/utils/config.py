"""环境变量统一加载。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 自动加载项目根目录的 .env
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / ".env")


def get_env(key: str, default: str = "") -> str:
    """获取环境变量，缺失时返回默认值。"""
    return os.getenv(key, default)


def require_env(key: str) -> str:
    """获取必填环境变量，缺失时抛出异常。"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"缺少必填环境变量: {key}")
    return value
