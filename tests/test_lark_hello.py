"""飞书 SDK 连通性测试。"""

import os

import pytest


@pytest.mark.skipif(
    not os.getenv("LARK_APP_ID"),
    reason="需要配置 LARK_APP_ID 环境变量",
)
def test_lark_client_init():
    """测试飞书客户端能否正常初始化。"""
    from feishu_adapter.base_client import FeishuBaseClient

    client = FeishuBaseClient()
    assert client.client is not None
