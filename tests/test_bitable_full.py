#!/usr/bin/env python3
"""
飞书多维表格完整功能测试
测试: 创建表、重命名、字段CRUD、写入mock数据
参考: Tables_schema.md
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("LARK_APP_ID")
APP_SECRET = os.getenv("LARK_APP_SECRET")
BASE_TOKEN = os.getenv("LARK_BASE_APP_TOKEN")

if not all([APP_ID, APP_SECRET, BASE_TOKEN]):
    print("[ERROR] 请配置 .env: LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN")
    sys.exit(1)

print("[TEST] 飞书多维表格完整功能测试\n")

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model.req_table import ReqTable
from lark_oapi.api.bitable.v1.model.app_table_create_header import AppTableCreateHeader
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody

client = Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()


def get_tenant_token():
    """获取 tenant_access_token"""
    resp = client.auth.v3.tenant_access_token.internal(
        InternalTenantAccessTokenRequest.builder()
            .request_body(InternalTenantAccessTokenRequestBody.builder()
                .app_id(APP_ID)
                .app_secret(APP_SECRET)
                .build())
            .build()
    )
    if resp.success():
        data = json.loads(resp.raw.content)
        return data.get('tenant_access_token')
    return None


def http_request(method, endpoint, data=None):
    """HTTP请求辅助函数"""
    import requests
    token = get_tenant_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"不支持的方法: {method}")
        # 检查内容类型
        content_type = resp.headers.get('content-type', '')
        if 'application/json' in content_type:
            return resp.json()
        else:
            # 非JSON响应
            return {"code": -1, "msg": f"非JSON响应: {resp.text[:100]}"}
    except Exception as e:
        return {"code": -1, "msg": str(e)}


# ==================== 测试1: 列出所有表 ====================
print("[TEST 1] 列出所有表...")
try:
    resp = client.bitable.v1.app_table.list(
        ListAppTableRequest.builder().app_token(BASE_TOKEN).build()
    )
    if resp.success():
        tables = {t.name: t.table_id for t in resp.data.items}
        print(f"   [OK] 发现 {len(tables)} 个表:")
        for name, tid in tables.items():
            print(f"        - {name}: {tid}")
    else:
        print(f"   [ERROR] {resp.msg}")
        tables = {}
except Exception as e:
    print(f"   [ERROR] {e}")
    tables = {}

# ==================== 测试2: 创建新表 ====================
print("\n[TEST 2] 创建测试表...")
TEST_TABLE_NAME = "TestInfoSource"
table_id = None

try:
    resp = client.bitable.v1.app_table.create(
        CreateAppTableRequest.builder()
            .app_token(BASE_TOKEN)
            .request_body(CreateAppTableRequestBody.builder()
                .table(
                    ReqTable.builder()
                        .name(TEST_TABLE_NAME)
                        .fields([
                            AppTableCreateHeader.builder().field_name("标题").type(1).build(),
                            AppTableCreateHeader.builder().field_name("状态").type(1).build(),
                        ])
                        .build()
                )
                .build()
            )
            .build()
    )
    if resp.success():
        table_id = resp.data.table_id
        print(f"   [OK] 表创建成功: {table_id}")
    else:
        print(f"   [WARN] 创建失败: {resp.msg}")
        print(f"   [INFO] 提示: 应用缺少创建表权限,将使用已有表测试")
except Exception as e:
    print(f"   [WARN] 异常: {e}")

# 如果创建失败,使用已有表
if not table_id:
    if tables:
        table_id = list(tables.values())[0]
        TEST_TABLE_NAME = list(tables.keys())[0]
        print(f"   [INFO] 使用已有表 '{TEST_TABLE_NAME}': {table_id}")
    else:
        print("   [ERROR] 无可用表,测试终止")
        sys.exit(1)

# ==================== 测试3: 重命名表 ====================
print("\n[TEST 3] 重命名表...")
try:
    from lark_oapi.api.bitable.v1.model.patch_app_table_request import PatchAppTableRequest, PatchAppTableRequestBody

    new_name = f"{TEST_TABLE_NAME}_Renamed"
    resp = client.bitable.v1.app_table.patch(
        PatchAppTableRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .request_body(PatchAppTableRequestBody.builder().name(new_name).build())
            .build()
    )
    if resp.success():
        print(f"   [OK] 表重命名成功: {new_name}")
        # 改回原名
        resp2 = client.bitable.v1.app_table.patch(
            PatchAppTableRequest.builder()
                .app_token(BASE_TOKEN)
                .table_id(table_id)
                .request_body(PatchAppTableRequestBody.builder().name(TEST_TABLE_NAME).build())
                .build()
        )
        if resp2.success():
            print(f"   [OK] 表名恢复成功")
    else:
        print(f"   [WARN] 重命名失败: {resp.msg}")
        if "permission" in resp.msg.lower() or "role" in resp.msg.lower():
            print(f"   [TIP] 提示: 应用需要添加到Base协作者中才能修改表结构")
except Exception as e:
    print(f"   [WARN] 重命名异常: {e}")

# ==================== 测试4: 列出字段 ====================
print("\n[TEST 4] 列出表字段...")
try:
    resp = client.bitable.v1.app_table_field.list(
        ListAppTableFieldRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .build()
    )
    if resp.success():
        fields = [(f.field_id, f.field_name) for f in resp.data.items]
        print(f"   [OK] 发现 {len(fields)} 个字段:")
        for fid, fname in fields:
            print(f"        - {fid}: {fname}")
    else:
        print(f"   [ERROR] {resp.msg}")
        fields = []
except Exception as e:
    print(f"   [ERROR] {e}")
    fields = []

# ==================== 测试5: 添加字段 ====================
print("\n[TEST 5] 添加字段...")
new_fields = ["优先级", "标签", "完成时间"]
field_id_map = {}

for field_name in new_fields:
    try:
        result = http_request(
            "POST",
            f"/tables/{table_id}/fields",
            {"field_name": field_name, "type": 1}  # 文本类型
        )
        if result.get("code") == 0:
            field_id = result.get("data", {}).get("field", {}).get("field_id")
            field_id_map[field_name] = field_id
            print(f"   [OK] 添加字段 '{field_name}': {field_id}")
        else:
            print(f"   [WARN] '{field_name}': {result.get('msg')}")
    except Exception as e:
        print(f"   [ERROR] '{field_name}': {e}")

# ==================== 测试6: 重命名字段 ====================
print("\n[TEST 6] 重命名字段...")
if "优先级" in field_id_map:
    try:
        field_id = field_id_map["优先级"]
        result = http_request(
            "PUT",
            f"/tables/{table_id}/fields/{field_id}",
            {"field_name": "优先级_Renamed"}
        )
        if result.get("code") == 0:
            print(f"   [OK] 字段重命名成功")
            # 改回原名
            result2 = http_request(
                "PUT",
                f"/tables/{table_id}/fields/{field_id}",
                {"field_name": "优先级"}
            )
            if result2.get("code") == 0:
                print(f"   [OK] 字段名恢复成功")
        else:
            print(f"   [WARN] 重命名字段失败: {result.get('msg')}")
    except Exception as e:
        print(f"   [WARN] 重命名字段异常: {e}")

# ==================== 测试7: 删除字段 ====================
print("\n[TEST 7] 删除字段...")
if "完成时间" in field_id_map:
    try:
        field_id = field_id_map["完成时间"]
        result = http_request("DELETE", f"/tables/{table_id}/fields/{field_id}")
        if result.get("code") == 0:
            print(f"   [OK] 删除字段 '完成时间' 成功")
            del field_id_map["完成时间"]
        else:
            print(f"   [WARN] 删除字段失败: {result.get('msg')}")
    except Exception as e:
        print(f"   [WARN] 删除字段异常: {e}")

# ==================== 测试8: 写入mock数据 ====================
print("\n[TEST 8] 写入mock数据...")

# 根据Tables_schema.md的SRC表创建mock数据
mock_data_src = {
    "id": "SRC-001",
    "源名称": "arXiv AI 论文",
    "源类型": "API",
    "平台": "arXiv",
    "API端点": "https://export.arxiv.org/api/query?search_query=cat:cs.AI",
    "监控关键词": ["AI", "LLM", "Agent", "RAG"],
    "抓取频率": "每小时",
    "权重": 0.95,
    "启用状态": "启用",
    "最近抓取时间": "2026-05-03T14:30:00",
    "平均响应时间": 1200,
    "抓取成功率": 98
}

# 简化版:只写入文本字段
text_fields = [f[1] for f in fields if f[1]] + list(field_id_map.keys())
print(f"   [INFO] 可用文本字段: {text_fields[:5]}...")

# 写入单条记录
try:
    # 构建字段数据(只使用表中存在的字段)
    record_fields = {}
    if "标题" in text_fields:
        record_fields["标题"] = "arXiv AI 论文源"
    if "状态" in text_fields:
        record_fields["状态"] = "启用"
    if "优先级" in text_fields or "优先级_Renamed" in text_fields:
        record_fields["优先级"] = "高"
    if "标签" in text_fields:
        record_fields["标签"] = "AI, LLM, Agent"

    resp = client.bitable.v1.app_table_record.create(
        CreateAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .request_body({"fields": record_fields})
            .build()
    )
    if resp.success():
        record_id = resp.data.record.record_id
        print(f"   [OK] 创建记录: {record_id[:20]}...")

        # 更新记录
        update_fields = {}
        if "内容" in text_fields:
            update_fields["内容"] = "已更新内容"
        elif "标题" in text_fields:
            update_fields["标题"] = "已更新标题"

        if update_fields:
            resp2 = client.bitable.v1.app_table_record.update(
                UpdateAppTableRecordRequest.builder()
                    .app_token(BASE_TOKEN)
                    .table_id(table_id)
                    .record_id(record_id)
                    .request_body({"fields": update_fields})
                    .build()
            )
            print(f"   [{'OK' if resp2.success() else 'ERROR'}] 更新记录")
        else:
            print(f"   [SKIP] 无可用字段用于更新")

        # 查询记录
        resp3 = client.bitable.v1.app_table_record.get(
            GetAppTableRecordRequest.builder()
                .app_token(BASE_TOKEN)
                .table_id(table_id)
                .record_id(record_id)
                .build()
        )
        print(f"   [{'OK' if resp3.success() else 'ERROR'}] 查询记录")

        # 删除记录
        resp4 = client.bitable.v1.app_table_record.delete(
            DeleteAppTableRecordRequest.builder()
                .app_token(BASE_TOKEN)
                .table_id(table_id)
                .record_id(record_id)
                .build()
        )
        print(f"   [{'OK' if resp4.success() else 'ERROR'}] 删除记录")
    else:
        print(f"   [ERROR] 创建记录失败: {resp.msg}")
except Exception as e:
    print(f"   [ERROR] 记录操作异常: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试9: 批量写入mock数据 ====================
print("\n[TEST 9] 批量写入mock数据...")
try:
    # 批量创建多条记录
    batch_records = []
    for i in range(3):
        record_fields = {}
        if "标题" in text_fields:
            record_fields["标题"] = f"测试记录-{i+1}"
        if "内容" in text_fields:
            record_fields["内容"] = f"内容-{i+1}"
        if record_fields:
            batch_records.append({"fields": record_fields})

    if batch_records:
        resp = client.bitable.v1.app_table_record.batch_create(
            BatchCreateAppTableRecordRequest.builder()
                .app_token(BASE_TOKEN)
                .table_id(table_id)
                .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch_records).build())
                .build()
        )
        if resp.success():
            print(f"   [OK] 批量创建 {len(batch_records)} 条记录")
        else:
            print(f"   [ERROR] 批量创建失败: {resp.msg}")
except Exception as e:
    print(f"   [ERROR] 批量创建异常: {e}")

# ==================== 测试10: 查询所有记录 ====================
print("\n[TEST 10] 查询所有记录...")
try:
    resp = client.bitable.v1.app_table_record.list(
        ListAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .build()
    )
    if resp.success():
        total = resp.data.total
        print(f"   [OK] 表中共有 {total} 条记录")
        if resp.data.items:
            print(f"   [INFO] 最新记录示例:")
            record = resp.data.items[0]
            print(f"        ID: {record.record_id[:20]}...")
            # 安全地打印字段
            fields_dict = getattr(record, 'fields', {}) or {}
            for k, v in list(fields_dict.items())[:3]:
                print(f"        {k}: {str(v)[:30]}...")
    else:
        print(f"   [ERROR] 查询失败: {resp.msg}")
except Exception as e:
    print(f"   [ERROR] 查询异常: {e}")

print("\n" + "=" * 50)
print("[DONE] 飞书多维表格完整功能测试结束!")
print(f"[INFO] Base链接: https://jcneyh7qlo8i.feishu.cn/base/{BASE_TOKEN}")
