"""信息源采集测试。"""

import pytest


@pytest.mark.asyncio
async def test_arxiv_source():
    """测试 arXiv 信息源能否正常采集。"""
    from core.sources.arxiv import ArxivSource

    source = ArxivSource()
    results = await source.fetch(limit=3)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_mock_xiaohongshu():
    """测试小红书 Mock 数据源。"""
    from core.sources.mock_xiaohongshu import MockXiaohongshuSource

    source = MockXiaohongshuSource()
    results = await source.fetch(limit=2)
    assert isinstance(results, list)
    if results:
        assert "source" in results[0]
