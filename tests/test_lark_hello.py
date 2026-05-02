#!/usr/bin/env python3
"""
lark-oapi Hello World - 简化版
验证：连接飞书 → 列出表 → 写入记录 → 读取记录
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# 凭证检查
APP_ID = os.getenv("LARK_APP_ID")
APP_SECRET = os.getenv("LARK_APP_SECRET")
BASE_TOKEN = os.getenv("LARK_BASE_APP_TOKEN")
TABLE_ID = os.getenv("LARK_TABLE_ID")  # 可选

if not all([APP_ID, APP_SECRET, BASE_TOKEN]):
    print("❌ 错误：请在 .env 文件中配置：")
    print("   - LARK_APP_ID")
    print("   - LARK_APP_SECRET")
    print("   - LARK_BASE_APP_TOKEN")
    print("\n可选：- LARK_TABLE_ID=xxx  # 已有表ID")
    sys.exit(1)

print("🚀 开始 lark-oapi Hello World 测试\n")
print(f"APP_ID: {APP_ID[:8]}...")
print(f"BASE_TOKEN: {BASE_TOKEN[:12]}...\n")

try:
    from lark_oapi import Client
    from lark_oapi.api.bitable.v1 import (
        ListAppTableRequest,
        ListAppTableRecordRequest,
        CreateAppTableRecordRequest
    )

    # 1. 创建客户端
    client = Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .build()
    print("✅ 客户端创建成功\n")

    # 2. 列出所有表
    print("📋 步骤1：查询 Base 中的所有表...")
    list_req = ListAppTableRequest.builder() \
        .app_token(BASE_TOKEN) \
        .build()
    list_resp = client.bitable.v1.app_table.list(list_req)

    if not list_resp.success():
        print(f"❌ 查询表失败: {list_resp.msg}")
        print(f"   错误码: {list_resp.code}")
        sys.exit(1)

    tables = list_resp.data.items
    print(f"✅ 查询成功，Base 中共有 {len(tables)} 个表：")
    for table in tables:
        print(f"   - {table.name} (ID: {table.table_id})")
    print()

    # 3. 获取要操作的表ID
    table_id = TABLE_ID
    if not table_id and tables:
        # 自动用第一个表
        table_id = tables[0].table_id
        print(f"📝 自动选择表: {tables[0].name} (ID: {table_id})\n")
    elif not table_id:
        print("⚠️  Base 中没有表，且未提供 TABLE_ID")
        print("    请在多维表格中手动创建一张表，或设置 LARK_TABLE_ID")
        sys.exit(1)
    else:
        print(f"📝 使用指定表 ID: {table_id}\n")

    # 4. 写入测试记录
    print("📝 步骤2：写入测试记录...")

    # 构建记录（匹配你的表字段：标题、内容）
    fields = {
        "标题": "Hello World",
        "内容": "lark-oapi 连通性测试成功！"
    }

    # 直接用字典作为 request_body
    record_req = CreateAppTableRecordRequest.builder() \
        .app_token(BASE_TOKEN) \
        .table_id(table_id) \
        .request_body({"fields": fields}) \
        .build()

    record_resp = client.bitable.v1.app_table_record.create(record_req)

    if not record_resp.success():
        print(f"❌ 写入记录失败: {record_resp.msg}")
        print(f"   错误码: {record_resp.code}")
        print("\n💡 提示：请确认表中是否有'标题'和'内容'字段")
        sys.exit(1)

    record_id = record_resp.data.record.record_id
    print(f"✅ 记录写入成功！ID: {record_id}\n")

    # 5. 查询记录
    print("📖 步骤3：查询表中所有记录...")
    query_req = ListAppTableRecordRequest.builder() \
        .app_token(BASE_TOKEN) \
        .table_id(table_id) \
        .build()
    query_resp = client.bitable.v1.app_table_record.list(query_req)

    if not query_resp.success():
        print(f"❌ 查询记录失败: {query_resp.msg}")
        sys.exit(1)

    total = query_resp.data.total
    items = query_resp.data.items or []
    print(f"✅ 查询成功，表中共有 {total} 条记录\n")

    print("最新5条记录：")
    for item in items[:5]:
        print(f"   - {item.fields}")

    print("\n" + "=" * 50)
    print("🎉 lark-oapi Hello World 测试通过！")
    print("=" * 50)
    print(f"\n🔗 Base 链接: https://jcneyh7qlo8i.feishu.cn/base/{BASE_TOKEN}")
    if tables:
        print(f"📝 操作表: {tables[0].name}")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("   请运行: pip install lark-oapi python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
