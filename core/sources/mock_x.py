"""X (Twitter) Mock 数据源。"""

import json
from pathlib import Path
from typing import Any

from core.sources.base import BaseSource


class MockXSource(BaseSource):
    name = "x"

    async def fetch(self, limit: int = 10) -> list[dict[str, Any]]:
        data_path = Path(__file__).parent.parent.parent / "mock_data" / "x_hot.json"
        if not data_path.exists():
            return []
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        return data[:limit]
