"""小哨 Agent E2E 测试。

测试完整流程：
1. 从信源配置读取启用的信源
2. 抓取信息
3. LLM分析（使用Mock）
4. 写入热帖池
5. 记录工作日志
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.trend_scout import TrendScoutAgent
from core.storage.id_generator import IDGenerator


class MockStorage:
    """Mock Storage 用于测试。"""

    def __init__(self):
        self.tables = {
            "信源配置": [],
            "热帖池": [],
            "Agent协作日志": [],
        }

    def query(self, table, filters=None, limit=100):
        """模拟查询。"""
        from core.storage.interface import StorageRecord

        records = self.tables.get(table, [])
        # 简单过滤
        if filters:
            for f in filters:
                if f.field == "是否启用" and f.operator == "eq":
                    records = [r for r in records if r.data.get("是否启用") == f.value]

        return records[:limit]

    def create(self, table, data):
        """模拟创建记录。"""
        from core.storage.interface import StorageRecord

        if table not in self.tables:
            self.tables[table] = []

        record = StorageRecord(
            id=data.get("业务ID", data.get("id", "test-id")),
            table=table,
            data=data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.tables[table].append(record)
        return record.id


class MockLLM:
    """Mock LLM 用于测试。"""

    def invoke(self, prompt):
        """返回固定的分析结果。"""
        return json.dumps({
            "热度评分": 0.85,
            "内容质量": "高",
            "主题标签": ["AI", "大模型", "技术突破"]
        })


def setup_mock_sources(storage):
    """设置Mock信源配置。"""
    sources = [
        {
            "业务ID": "SRC-20260504-001",
            "平台": "小红书",
            "类型": "Mock数据",
            "是否启用": True,
            "每次抓取上限": 2,
            "配置JSON": "{}",
        },
        {
            "业务ID": "SRC-20260504-002",
            "平台": "抖音",
            "类型": "Mock数据",
            "是否启用": True,
            "每次抓取上限": 2,
            "配置JSON": "{}",
        },
        {
            "业务ID": "SRC-20260504-003",
            "平台": "X",
            "类型": "Mock数据",
            "是否启用": False,  # 未启用，不应被抓取
            "每次抓取上限": 2,
            "配置JSON": "{}",
        },
    ]

    from core.storage.interface import StorageRecord
    for src in sources:
        record = StorageRecord(
            id=src["业务ID"],
            table="信源配置",
            data=src,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage.tables["信源配置"].append(record)


def test_trend_scout_full_flow():
    """测试小哨完整流程。"""
    print("=" * 60)
    print("测试: TrendScout Agent 完整流程")
    print("=" * 60)

    # 重置ID生成器
    IDGenerator.reset()

    # 创建Mock依赖
    storage = MockStorage()
    llm = MockLLM()

    # 设置Mock信源
    setup_mock_sources(storage)

    # 创建Agent
    agent = TrendScoutAgent(storage, llm)

    # 执行
    context = {
        "koc": {
            "领域": ["AI", "大模型", "编程"],
        }
    }

    result = agent.execute(context)

    # 验证结果
    print(f"\n[OK] 执行完成，抓取 {result.get('count', 0)} 条热帖")

    # 验证热帖池写入
    hot_posts = storage.tables.get("热帖池", [])
    print(f"[OK] 热帖池记录数: {len(hot_posts)}")

    # 验证日志写入
    logs = storage.tables.get("Agent协作日志", [])
    print(f"[OK] 协作日志记录数: {len(logs)}")

    # 验证数据完整性
    if hot_posts:
        post = hot_posts[0].data
        print(f"\n热帖示例:")
        print(f"  - 业务ID: {post.get('业务ID')}")
        print(f"  - 标题: {post.get('标题')[:50]}...")
        print(f"  - 信源平台: {post.get('信源平台')}")
        print(f"  - 热度评分: {post.get('热度评分')}")
        print(f"  - 内容质量: {post.get('内容质量')}")
        print(f"  - 主题标签: {post.get('主题标签')}")
        print(f"  - 状态: {post.get('状态')}")

    # 断言验证
    assert result.get("count") > 0, "应至少抓取到1条热帖"
    assert len(hot_posts) == result.get("count"), "热帖池记录数应与抓取数一致"
    assert len(logs) == 1, "应写入1条协作日志"

    print("\n" + "=" * 60)
    print("[PASS] 所有测试通过！")
    print("=" * 60)

    return True


def test_trend_scout_no_enabled_sources():
    """测试没有启用信源的情况。"""
    print("\n" + "=" * 60)
    print("测试: 无启用信源场景")
    print("=" * 60)

    storage = MockStorage()
    llm = MockLLM()

    # 不添加任何启用的信源
    agent = TrendScoutAgent(storage, llm)

    context = {"koc": {"领域": ["AI"]}}
    result = agent.execute(context)

    assert result.get("count", 0) == 0, "无启用信源时应返回0条"
    print("[OK] 无启用信源时正确处理")

    return True


def test_id_generator():
    """测试ID生成器。"""
    print("\n" + "=" * 60)
    print("测试: ID生成器")
    print("=" * 60)

    IDGenerator.reset()

    # 生成多个ID
    id1 = IDGenerator.generate("TREND")
    id2 = IDGenerator.generate("TREND")
    id3 = IDGenerator.generate("TOPIC")

    print(f"ID1: {id1}")
    print(f"ID2: {id2}")
    print(f"ID3: {id3}")

    # 验证格式
    assert id1.startswith("TREND-"), "ID应以TREND-开头"
    assert id2.startswith("TREND-"), "ID应以TREND-开头"
    assert id3.startswith("TOPIC-"), "ID应以TOPIC-开头"

    # 验证序号递增
    assert id1 != id2, "连续生成的ID应不同"

    print("[OK] ID生成器工作正常")

    return True


if __name__ == "__main__":
    try:
        test_id_generator()
        test_trend_scout_full_flow()
        test_trend_scout_no_enabled_sources()
        print("\n[SUCCESS] 所有测试通过！")
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
