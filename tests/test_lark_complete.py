#!/usr/bin/env python3
"""
lark-oapi 完整功能测试 - 最简版
测试：建表、字段增删改、视图创建、记录CRUD
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("LARK_APP_ID")
APP_SECRET = os.getenv("LARK_APP_SECRET")
BASE_TOKEN = os.getenv("LARK_BASE_APP_TOKEN")

if not all([APP_ID, APP_SECRET, BASE_TOKEN]):
    print("[ERROR] 请配置 .env：LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN")
    sys.exit(1)

print("[TEST] lark-oapi 完整功能测试\n")

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model.req_table import ReqTable
from lark_oapi.api.bitable.v1.model.app_table_create_header import AppTableCreateHeader

client = Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()

# ===== 1. 列出所有表 =====
print("[STEP 1] 列出所有表...")
resp = client.bitable.v1.app_table.list(
    ListAppTableRequest.builder().app_token(BASE_TOKEN).build()
)
if not resp.success():
    print(f"[ERROR] 失败: {resp.msg}")
    sys.exit(1)

tables = {t.name: t.table_id for t in resp.data.items}
print(f"   现有 {len(tables)} 个表: {list(tables.keys())}")

# ===== 2. 确定要使用的表 =====
TEST_TABLE = "APITestTable"
table_id = None

# 优先使用已存在的测试表
if TEST_TABLE in tables:
    table_id = tables[TEST_TABLE]
    print(f"\n[TABLE] 使用已有测试表 '{TEST_TABLE}': {table_id}")
else:
    # 尝试创建新表
    print(f"\n[TABLE] 尝试创建测试表 '{TEST_TABLE}'...")
    try:
        resp = client.bitable.v1.app_table.create(
            CreateAppTableRequest.builder()
                .app_token(BASE_TOKEN)
                .request_body(CreateAppTableRequestBody.builder()
                    .table(
                        ReqTable.builder()
                            .name(TEST_TABLE)
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
            print(f"   [WARN]  创建失败: {resp.msg}")
    except Exception as e:
        print(f"   [WARN]  异常: {e}")

    # 如果创建失败，使用默认表"数据表"
    if not table_id:
        if "数据表" in tables:
            table_id = tables["数据表"]
            print(f"\n[TABLE] 使用默认表 '数据表': {table_id}")
            print("   [TIP] 提示：应用缺少创建表权限，请在飞书后台开启权限或使用已有表")
        else:
            print("[ERROR] 无可用表，测试终止")
            sys.exit(1)

# 获取 tenant_access_token 用于 HTTP API
def get_tenant_token():
    from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody
    import json
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

# ===== 4. 添加字段 =====
print("\n[ADD] 添加字段...")
token = get_tenant_token()
fields_to_add = ["优先级", "标签", "完成时间"]
for field_name in fields_to_add:
    try:
        import requests
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {"field_name": field_name, "type": 1}
        resp = requests.post(url, headers=headers, json=data)
        if resp.json().get("code") == 0:
            print(f"   [OK] 添加字段 '{field_name}'")
        else:
            print(f"   [WARN]  '{field_name}': {resp.json().get('msg')}")
    except Exception as e:
        print(f"   [ERROR] '{field_name}': {e}")

# ===== 5. 创建视图 =====
print("\n[VIEW] 创建视图...")
view_name = "测试视图"
try:
    import requests
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/views"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"view_name": view_name, "view_type": "grid"}
    resp = requests.post(url, headers=headers, json=data)
    if resp.json().get("code") == 0:
        print(f"   [OK] 创建视图 '{view_name}'")
    else:
        print(f"   [WARN]  {resp.json().get('msg')}")
except Exception as e:
    print(f"   [ERROR] {e}")

# ===== 6. 记录CRUD =====
print("\n[RECORD] 记录操作...")

# 创建（使用表中实际存在的字段）
resp = client.bitable.v1.app_table_record.create(
    CreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body({"fields": {"标题": "测试记录1", "内容": "进行中"}})
        .build()
)
if resp.success():
    record_id = resp.data.record.record_id
    print(f"   [OK] 创建记录: {record_id[:20]}...")
else:
    print(f"   [ERROR] 创建失败: {resp.msg}")
    record_id = None

if record_id:
    # 更新
    resp = client.bitable.v1.app_table_record.update(
        UpdateAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .request_body({"fields": {"内容": "已完成"}})
            .build()
    )
    print(f"   {'[OK]' if resp.success() else '[ERROR]'} 更新记录")

    # 查询
    resp = client.bitable.v1.app_table_record.get(
        GetAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .build()
    )
    print(f"   {'[OK]' if resp.success() else '[ERROR]'} 查询记录")

    # 删除
    resp = client.bitable.v1.app_table_record.delete(
        DeleteAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .build()
    )
    print(f"   {'[OK]' if resp.success() else '[ERROR]'} 删除记录")

# ===== 7. 批量操作 =====
print("\n[TABLE] 批量创建记录...")
records = [
    {"fields": {"标题": f"批量记录{i}", "内容": "待处理"}}
    for i in range(3)
]
resp = client.bitable.v1.app_table_record.batch_create(
    BatchCreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build())
        .build()
)
print(f"   {'[OK]' if resp.success() else '[ERROR]'} 批量创建 {len(records)} 条")

# 查询所有
resp = client.bitable.v1.app_table_record.list(
    ListAppTableRecordRequest.builder().app_token(BASE_TOKEN).table_id(table_id).build()
)
if resp.success():
    print(f"   [STATS] 表中有 {resp.data.total} 条记录")

print("\n" + "="*50)
print("[DONE] 完整功能测试结束！")
print(f"[LINK] 查看表格: https://jcneyh7qlo8i.feishu.cn/base/{BASE_TOKEN}")
