#!/usr/bin/env python3
"""
测试对飞书多维表格中的文档进行增删改操作
目标表格: TestInfoSource (从截图中看到的)
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils.feishu_base import FeishuBaseManager


def test_document_crud():
    """测试文档的增删改查操作"""

    print("=" * 60)
    print("飞书多维表格 - 记录增删改测试")
    print("=" * 60)

    # 初始化管理器
    try:
        base = FeishuBaseManager()
        print("\n[OK] 初始化成功")
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        print("请检查 .env 文件中的 LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN")
        return

    # 列出所有表
    try:
        tables = base.list_tables()
        print(f"\n[OK] 发现 {len(tables)} 个表:")
        for name, tid in tables.items():
            print(f"      - {name}: {tid}")
    except Exception as e:
        print(f"\n[ERROR] 获取表列表失败: {e}")
        return

    # 查找 TestInfoSource 表
    table_name = "TestInfoSource"
    if table_name not in tables:
        print(f"\n[ERROR] 未找到表 '{table_name}'")
        print("请确认表格名称，或修改 table_name 变量为存在的表名")
        return

    table_id = tables[table_name]
    print(f"\n[INFO] 使用表 '{table_name}': {table_id}")

    # 列出表的字段
    try:
        fields = base.list_fields(table_id)
        print(f"\n[OK] 表字段列表:")
        for fname, fid in fields.items():
            print(f"      - {fname}: {fid}")
    except Exception as e:
        print(f"\n[ERROR] 获取字段列表失败: {e}")
        fields = {}

    # 测试记录ID（用于存储创建的记录，便于后续操作）
    test_record_id = None

    # ==================== 1. 创建记录 (CREATE) ====================
    print("\n" + "-" * 60)
    print("[TEST 1] 创建新记录")
    print("-" * 60)

    try:
        # 根据实际字段构建数据
        record_data = {}

        # 如果表中有"标题"或"名称"字段
        if "标题" in fields:
            record_data["标题"] = f"测试文档-{datetime.now().strftime('%H:%M:%S')}"
        elif "名称" in fields:
            record_data["名称"] = f"测试文档-{datetime.now().strftime('%H:%M:%S')}"
        elif "标题" in fields:
            record_data["标题"] = f"测试文档-{datetime.now().strftime('%H:%M:%S')}"
        else:
            # 使用第一个字段
            first_field = list(fields.keys())[0] if fields else None
            if first_field:
                record_data[first_field] = "测试内容"

        # 添加其他常见字段
        if "内容" in fields:
            record_data["内容"] = "这是由自动测试脚本创建的内容"
        if "状态" in fields:
            record_data["状态"] = "新建"
        if "类型" in fields:
            record_data["类型"] = "测试"
        if "时间" in fields:
            record_data["时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[INFO] 准备创建记录，数据:")
        for k, v in record_data.items():
            print(f"       {k}: {v}")

        # 创建记录
        test_record_id = base.create_record(table_id, record_data)
        print(f"\n[OK] 记录创建成功!")
        print(f"[INFO] 记录ID: {test_record_id}")

    except Exception as e:
        print(f"\n[ERROR] 创建记录失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==================== 2. 查询记录 (READ) ====================
    print("\n" + "-" * 60)
    print("[TEST 2] 查询记录")
    print("-" * 60)

    try:
        # 查询刚创建的记录
        record = base.get_record(table_id, test_record_id)
        print(f"[OK] 查询成功!")
        print(f"[INFO] 记录详情:")
        print(f"       ID: {record['record_id']}")
        print(f"       字段数据:")
        for field_name, field_value in record['fields'].items():
            print(f"         - {field_name}: {field_value}")

    except Exception as e:
        print(f"\n[ERROR] 查询记录失败: {e}")

    # ==================== 3. 更新记录 (UPDATE) ====================
    print("\n" + "-" * 60)
    print("[TEST 3] 更新记录")
    print("-" * 60)

    try:
        # 构建更新数据
        update_data = {}

        # 更新现有字段
        if "状态" in fields:
            update_data["状态"] = "已更新"
        if "内容" in fields:
            update_data["内容"] = "这条记录的内容已被更新！\n更新时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "标题" in fields:
            update_data["标题"] = f"已更新的标题-{datetime.now().strftime('%H:%M:%S')}"
        elif "名称" in fields:
            update_data["名称"] = f"已更新的名称-{datetime.now().strftime('%H:%M:%S')}"

        if not update_data:
            # 如果没有匹配的字段，更新第一个字段
            first_field = list(fields.keys())[0] if fields else None
            if first_field:
                update_data[first_field] = "已更新值"

        print(f"[INFO] 准备更新，数据:")
        for k, v in update_data.items():
            print(f"       {k}: {v}")

        # 执行更新
        success = base.update_record(table_id, test_record_id, update_data)
        if success:
            print(f"\n[OK] 记录更新成功!")

            # 验证更新结果
            updated_record = base.get_record(table_id, test_record_id)
            print(f"\n[INFO] 更新后的记录:")
            for field_name, field_value in updated_record['fields'].items():
                print(f"       - {field_name}: {field_value}")
        else:
            print(f"\n[ERROR] 更新记录失败")

    except Exception as e:
        print(f"\n[ERROR] 更新记录失败: {e}")
        import traceback
        traceback.print_exc()

    # ==================== 4. 删除记录 (DELETE) ====================
    print("\n" + "-" * 60)
    print("[TEST 4] 删除记录")
    print("-" * 60)

    try:
        # 自动删除（设置为False则保留记录）
        auto_delete = True

        if auto_delete:
            success = base.delete_record(table_id, test_record_id)
            if success:
                print(f"[OK] 记录删除成功!")
            else:
                print(f"[ERROR] 删除记录失败")
        else:
            print(f"[INFO] 跳过删除操作，记录保留")
            print(f"[INFO] 记录ID: {test_record_id}")

    except Exception as e:
        print(f"\n[ERROR] 删除记录失败: {e}")
        import traceback
        traceback.print_exc()

    # ==================== 5. 列出现有记录 ====================
    print("\n" + "-" * 60)
    print("[TEST 5] 列出表中所有记录")
    print("-" * 60)

    try:
        records = base.list_records(table_id)
        print(f"[OK] 表中共有 {len(records)} 条记录")

        if records:
            print(f"\n[INFO] 最新3条记录:")
            for i, record in enumerate(records[:3], 1):
                print(f"\n       [{i}] ID: {record['record_id'][:20]}...")
                fields_dict = record.get('fields', {})
                # 显示前3个字段
                for j, (k, v) in enumerate(list(fields_dict.items())[:3], 1):
                    print(f"           {k}: {str(v)[:40]}")

    except Exception as e:
        print(f"\n[ERROR] 列出记录失败: {e}")
        import traceback
        traceback.print_exc()

    # 完成
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"\n访问地址: https://jcneyh7qlo8i.feishu.cn/base/{os.getenv('LARK_BASE_APP_TOKEN')}")
    print(f"表格名称: {table_name}")


if __name__ == "__main__":
    test_document_crud()
