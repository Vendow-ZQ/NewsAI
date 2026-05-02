#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lark-oapi 最简测试 - 字段与视图操作
"""

import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("LARK_APP_ID")
APP_SECRET = os.getenv("LARK_APP_SECRET")
BASE_TOKEN = os.getenv("LARK_BASE_APP_TOKEN")

if not all([APP_ID, APP_SECRET, BASE_TOKEN]):
    print("ERROR: 配置 .env 文件")
    sys.exit(1)

# 获取 token
def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    return resp.json().get("tenant_access_token")

TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

print("lark-oapi 最简功能测试\n")

# 1. 列出所有表
print("1. 列出所有表...")
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables"
resp = requests.get(url, headers=HEADERS).json()

if resp.get("code") != 0:
    print(f"   FAILED: {resp.get('msg')}")
    sys.exit(1)

tables = resp["data"]["items"]
print(f"   找到 {len(tables)} 个表")
for t in tables:
    print(f"      - {t['name']}: {t['table_id']}")

# 使用第一个表或创建新表
if tables:
    table_id = tables[0]["table_id"]
    print(f"\n   使用表: {tables[0]['name']}\n")
else:
    print("\n   没有表，退出")
    sys.exit(1)

# 2. 列出字段
print("2. 列出字段...")
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/fields"
resp = requests.get(url, headers=HEADERS).json()
if resp.get("code") == 0:
    fields = resp["data"]["items"]
    print(f"   现有 {len(fields)} 个字段: {[f['field_name'] for f in fields]}")

# 3. 添加字段
print("\n3. 添加字段...")
new_fields = ["测试字段A", "测试字段B"]
for field_name in new_fields:
    data = {"field_name": field_name, "field_type": 1}  # 文本类型
    resp = requests.post(url, headers=HEADERS, json=data).json()
    if resp.get("code") == 0:
        print(f"   ADDED: {field_name}")
    else:
        print(f"   SKIP: {field_name} ({resp.get('msg')})")

# 4. 列出视图
print("\n4. 列出视图...")
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/views"
resp = requests.get(url, headers=HEADERS).json()
if resp.get("code") == 0:
    views = resp["data"]["items"]
    print(f"   现有 {len(views)} 个视图: {[v['view_name'] for v in views]}")

# 5. 创建视图
print("\n5. 创建视图...")
view_name = "API测试视图"
data = {"view_name": view_name, "view_type": "grid"}
resp = requests.post(url, headers=HEADERS, json=data).json()
if resp.get("code") == 0:
    print(f"   CREATED: {view_name}")
else:
    print(f"   SKIP: {view_name} ({resp.get('msg')})")

# 6. 记录 CRUD
print("\n6. 记录操作...")
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/records"

# 创建
resp = requests.post(url, headers=HEADERS, json={
    "fields": {"标题": "API测试记录", "测试字段A": "内容A"}
}).json()
if resp.get("code") == 0:
    record_id = resp["data"]["record"]["record_id"]
    print(f"   CREATED: {record_id[:20]}...")

    # 更新
    update_url = f"{url}/{record_id}"
    resp = requests.put(update_url, headers=HEADERS, json={
        "fields": {"测试字段B": "内容B"}
    }).json()
    print(f"   {'UPDATED' if resp.get('code') == 0 else 'FAILED'}")

    # 查询
    resp = requests.get(update_url, headers=HEADERS).json()
    print(f"   {'RETRIEVED' if resp.get('code') == 0 else 'FAILED'}")

    # 删除
    resp = requests.delete(update_url, headers=HEADERS).json()
    print(f"   {'DELETED' if resp.get('code') == 0 else 'FAILED'}")

# 7. 批量创建
print("\n7. 批量创建...")
records = [{"fields": {"标题": f"批量{i}"}} for i in range(3)]
resp = requests.post(f"{url}/batch_create", headers=HEADERS, json={"records": records}).json()
if resp.get("code") == 0:
    print(f"   BATCH CREATED: {len(records)} records")

# 最终统计
print("\n8. 统计...")
resp = requests.get(url, headers=HEADERS).json()
if resp.get("code") == 0:
    total = resp["data"].get("total", 0)
    print(f"   TOTAL RECORDS: {total}")

print("\n" + "="*50)
print("TEST COMPLETE")
print(f"URL: https://jcneyh7qlo8i.feishu.cn/base/{BASE_TOKEN}")
