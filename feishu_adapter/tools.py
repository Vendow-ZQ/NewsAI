"""LangChain Tools 封装 -- 将飞书 base_client 包装为 Agent 可用的 Tool。"""

from langchain_core.tools import tool

from feishu_adapter.base_client import FeishuBaseClient

_client = FeishuBaseClient()


@tool
async def write_to_base(table_id: str, fields: str) -> str:
    """向飞书多维表格写入一条记录。"""
    import json
    fields_dict = json.loads(fields)
    result = await _client.create_record(table_id, fields_dict)
    return str(result)


@tool
async def read_from_base(table_id: str, filter_expr: str = "") -> str:
    """从飞书多维表格读取记录。"""
    import json
    records = await _client.query_records(table_id, filter_expr)
    return json.dumps(records, ensure_ascii=False)
