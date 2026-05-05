"""X (Twitter) Mock 数据源。"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime

from core.sources.base import BaseSource


class MockXSource(BaseSource):
    name = "X"

    def fetch(self, limit: int = 10, config: dict = None) -> list[dict[str, Any]]:
        """从Mock数据文件读取X热门内容。"""
        data_path = Path(__file__).parent.parent.parent / "mock_data" / "x_hot.json"
        if not data_path.exists():
            return []
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        # 确保limit是整数
        limit = int(limit) if limit else len(data)
        items = list(data)[:limit]

        # 转换字段名以匹配标准格式
        results = []
        for item in items:
            results.append({
                "标题": item.get("title", ""),
                "原文链接": item.get("url", ""),
                "原文摘要": item.get("summary", "")[:500] if item.get("summary") else "",
                "原文语言": "英文",
                "发布时间": item.get("published_at", datetime.now().isoformat()),
                "信源平台": "X",
            })
        return results
