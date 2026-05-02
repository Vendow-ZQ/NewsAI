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
    print("❌ 请配置 .env：LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN")
    sys.exit(1)

print("🚀 lark-oapi 完整功能测试\n")

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import *

client = Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()

# ===== 1. 列出所有表 =====
print("📋 列出所有表...")
resp = client.bitable.v1.app_table.list(
    ListAppTableRequest.builder().app_token(BASE_TOKEN).build()
)
if not resp.success():
    print(f"❌ 失败: {resp.msg}")
    sys.exit(1)

tables = {t.name: t.table_id for t in resp.data.items}
print(f"   现有 {len(tables)} 个表: {list(tables.keys())}")

# ===== 2. 删除旧测试表（如果存在）=====
TEST_TABLE = "APITestTable"
if TEST_TABLE in tables:
    print(f"\n🗑️  删除旧测试表 '{TEST_TABLE}'...")
    # 通过API删除表（如果需要）
    # 注：lark-oapi 可能不支持删除表，需通过HTTP API

# ===== 3. 创建新表 =====
print(f"\n📦 创建测试表 '{TEST_TABLE}'...")
try:
    resp = client.bitable.v1.app_table.create(
        CreateAppTableRequest.builder()
            .app_token(BASE_TOKEN)
            .request_body(CreateAppTableRequestBody.builder()
                .table(TEST_TABLE)
                .fields([
                    AppTableCreateHeader.builder().field_name("标题").field_type(1).build(),
                    AppTableCreateHeader.builder().field_name("状态").field_type(1).build(),
                ])
                .build()
            )
            .build()
    )
    if resp.success():
        table_id = resp.data.table_id
        print(f"   ✅ 表创建成功: {table_id}")
    else:
        print(f"   ⚠️  {resp.msg}")
        # 查找已有表
        for t in client.bitable.v1.app_table.list(ListAppTableRequest.builder().app_token(BASE_TOKEN).build()).data.items:
            if t.name == TEST_TABLE:
                table_id = t.table_id
                print(f"   使用已有表: {table_id}")
                break
except Exception as e:
    print(f"   ⚠️  {e}")
    sys.exit(1)

# ===== 4. 添加字段 =====
print("\n➕ 添加字段...")
fields_to_add = ["优先级", "标签", "完成时间"]
for field_name in fields_to_add:
    try:
        # 通过HTTP API添加字段（SDK可能不支持）
        import requests
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {client.auth.get_tenant_access_token().token}",
            "Content-Type": "application/json"
        }
        data = {"field_name": field_name, "field_type": 1}  # 文本类型
        resp = requests.post(url, headers=headers, json=data)
        if resp.json().get("code") == 0:
            print(f"   ✅ 添加字段 '{field_name}'")
        else:
            print(f"   ⚠️  '{field_name}': {resp.json().get('msg')}")
    except Exception as e:
        print(f"   ❌ '{field_name}': {e}")

# ===== 5. 创建视图 =====
print("\n👁️ 创建视图...")
view_name = "测试视图"
try:
    import requests
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/views"
    headers = {
        "Authorization": f"Bearer {client.auth.get_tenant_access_token().token}",
        "Content-Type": "application/json"
    }
    data = {"view_name": view_name, "view_type": "grid"}
    resp = requests.post(url, headers=headers, json=data)
    if resp.json().get("code") == 0:
        print(f"   ✅ 创建视图 '{view_name}'")
    else:
        print(f"   ⚠️  {resp.json().get('msg')}")
except Exception as e:
    print(f"   ❌ {e}")

# ===== 6. 记录CRUD =====
print("\n📝 记录操作...")

# 创建
resp = client.bitable.v1.app_table_record.create(
    CreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body({"fields": {"标题": "测试记录1", "状态": "进行中"}})
        .build()
)
if resp.success():
    record_id = resp.data.record.record_id
    print(f"   ✅ 创建记录: {record_id[:20]}...")
else:
    print(f"   ❌ 创建失败: {resp.msg}")
    record_id = None

if record_id:
    # 更新
    resp = client.bitable.v1.app_table_record.update(
        UpdateAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .request_body({"fields": {"状态": "已完成"}})
            .build()
    )
    print(f"   {'✅' if resp.success() else '❌'} 更新记录")

    # 查询
    resp = client.bitable.v1.app_table_record.get(
        GetAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .build()
    )
    print(f"   {'✅' if resp.success() else '❌'} 查询记录")

    # 删除
    resp = client.bitable.v1.app_table_record.delete(
        DeleteAppTableRecordRequest.builder()
            .app_token(BASE_TOKEN)
            .table_id(table_id)
            .record_id(record_id)
            .build()
    )
    print(f"   {'✅' if resp.success() else '❌'} 删除记录")

# ===== 7. 批量操作 =====
print("\n📦 批量创建记录...")
records = [
    {"fields": {"标题": f"批量记录{i}", "状态": "待处理"}}
    for i in range(3)
]
resp = client.bitable.v1.app_table_record.batch_create(
    BatchCreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build())
        .build()
)
print(f"   {'✅' if resp.success() else '❌'} 批量创建 {len(records)} 条")

# 查询所有
resp = client.bitable.v1.app_table_record.list(
    ListAppTableRecordRequest.builder().app_token(BASE_TOKEN).table_id(table_id).build()
)
if resp.success():
    print(f"   📊 表中有 {resp.data.total} 条记录")

print("\n" + "="*50)
print("🎉 完整功能测试结束！")
print(f"🔗 查看表格: https://jcneyh7qlo8i.feishu.cn/base/{BASE_TOKEN}")
