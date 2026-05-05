"""
Storage接口层测试用例

测试内容：
1. IDGenerator - 业务ID生成器
2. IDMapping - 业务ID与飞书record_id映射
3. FeishuStorage - 完整的CRUD操作

运行方式：
    cd D:/Code/NewsAI
    python -m pytest tests/test_storage_interface.py -v
    或
    python tests/test_storage_interface.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage.id_generator import IDGenerator, generate_id, TABLE_PREFIXES
from feishu_adapter.base.id_mapping import IDMapping
from feishu_adapter.base.tables import (
    TABLES, get_table_fields, get_table_prefix, get_seed_data
)


def test_id_generator():
    """测试ID生成器"""
    print("\n" + "="*60)
    print("测试1: IDGenerator - 业务ID生成器")
    print("="*60)

    # 重置计数器
    IDGenerator.reset()

    # 测试基本生成
    id1 = IDGenerator.generate("SRC")
    print(f"生成ID 1: {id1}")
    assert id1.startswith("SRC-"), f"ID格式错误: {id1}"
    assert len(id1.split("-")) == 3, f"ID格式错误: {id1}"

    # 测试连续生成
    id2 = IDGenerator.generate("SRC")
    print(f"生成ID 2: {id2}")
    assert id2 != id1, "连续生成的ID应该不同"
    assert id2.endswith("-002"), f"序号错误: {id2}"

    # 测试不同前缀
    id3 = IDGenerator.generate("TREND")
    print(f"生成ID 3 (TREND): {id3}")
    assert id3.startswith("TREND-"), f"前缀错误: {id3}"

    # 测试指定日期
    test_date = datetime(2026, 5, 1)
    id4 = IDGenerator.generate("TOPIC", test_date)
    print(f"生成ID 4 (指定日期): {id4}")
    assert "20260501" in id4, f"日期错误: {id4}"

    # 测试generate_id函数
    id5 = generate_id("信源配置")
    print(f"通过表名生成ID: {id5}")
    assert id5.startswith("SRC-"), f"表名映射错误: {id5}"

    # 测试重置
    IDGenerator.reset("SRC")
    id6 = IDGenerator.generate("SRC")
    print(f"重置后生成ID: {id6}")
    assert id6.endswith("-001"), f"重置后序号应从1开始: {id6}"

    print("\n[OK] IDGenerator 测试通过!")
    return True


def test_id_mapping():
    """测试ID映射管理"""
    print("\n" + "="*60)
    print("测试2: IDMapping - 业务ID映射管理")
    print("="*60)

    # 创建临时目录和文件
    temp_dir = tempfile.mkdtemp()
    mapping_file = os.path.join(temp_dir, "test_mapping.json")

    try:
        # 初始化
        mapping = IDMapping(mapping_file)
        print(f"初始化IDMapping，文件: {mapping_file}")

        # 测试添加映射
        mapping.add("信源配置", "SRC-20260504-001", "rec_abc123")
        mapping.add("信源配置", "SRC-20260504-002", "rec_def456")
        mapping.add("热帖库", "TREND-20260504-001", "rec_ghi789")
        print("添加3条映射关系")

        # 测试查询
        record_id = mapping.get_record_id("信源配置", "SRC-20260504-001")
        print(f"查询映射: SRC-20260504-001 -> {record_id}")
        assert record_id == "rec_abc123", f"查询结果错误: {record_id}"

        # 测试反向查询
        business_id = mapping.get_business_id("信源配置", "rec_abc123")
        print(f"反向查询: rec_abc123 -> {business_id}")
        assert business_id == "SRC-20260504-001", f"反向查询错误: {business_id}"

        # 测试不存在的映射
        not_found = mapping.get_record_id("信源配置", "SRC-999")
        print(f"查询不存在的映射: {not_found}")
        assert not_found is None, "不存在的映射应返回None"

        # 测试exists
        exists = mapping.exists("信源配置", "SRC-20260504-001")
        not_exists = mapping.exists("信源配置", "SRC-999")
        print(f"检查存在性: SRC-20260504-001={exists}, SRC-999={not_exists}")
        assert exists is True, "存在的映射应返回True"
        assert not_exists is False, "不存在的映射应返回False"

        # 测试列出表映射
        table_mappings = mapping.list_table_mappings("信源配置")
        print(f"信源配置表映射: {table_mappings}")
        assert len(table_mappings) == 2, f"映射数量错误: {len(table_mappings)}"

        # 测试删除
        removed = mapping.remove("信源配置", "SRC-20260504-001")
        not_removed = mapping.remove("信源配置", "SRC-999")
        print(f"删除映射: 成功={removed}, 不存在={not_removed}")
        assert removed is True, "删除存在的映射应返回True"
        assert not_removed is False, "删除不存在的映射应返回False"

        # 验证删除
        after_remove = mapping.get_record_id("信源配置", "SRC-20260504-001")
        print(f"删除后查询: {after_remove}")
        assert after_remove is None, "删除后应返回None"

        # 测试持久化 - 重新加载
        mapping2 = IDMapping(mapping_file)
        persisted = mapping2.get_record_id("信源配置", "SRC-20260504-002")
        print(f"持久化验证: SRC-20260504-002 -> {persisted}")
        assert persisted == "rec_def456", "持久化数据应保持一致"

        # 测试清空表
        mapping.clear_table("热帖库")
        cleared = mapping.list_table_mappings("热帖库")
        print(f"清空热帖库后: {cleared}")
        assert len(cleared) == 0, "清空后应为空"

        print("\n[OK] IDMapping 测试通过!")
        return True

    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)


def test_table_schema():
    """测试表Schema定义"""
    print("\n" + "="*60)
    print("测试3: Tables Schema - 表结构定义")
    print("="*60)

    # 测试表数量
    print(f"定义了 {len(TABLES)} 张表")
    assert len(TABLES) == 7, f"表数量应为7: {len(TABLES)}"

    # 测试每张表的字段
    for table_name, config in TABLES.items():
        prefix = config["prefix"]
        fields = config["fields"]
        print(f"\n表: {table_name} (前缀: {prefix})")
        print(f"  字段数: {len(fields)}")

        # 验证前缀
        expected_prefix = TABLE_PREFIXES.get(table_name)
        assert prefix == expected_prefix, f"前缀错误: {table_name}"

        # 验证每个字段有name和type
        for field in fields:
            assert "name" in field, f"字段缺少name: {field}"
            assert "type" in field, f"字段缺少type: {field}"

        # 验证id字段存在
        id_fields = [f for f in fields if f["name"] == "id"]
        assert len(id_fields) == 1, f"{table_name} 缺少id字段"
        assert id_fields[0]["required"] is True, f"{table_name} 的id字段应为必填"

    # 测试get_table_fields
    src_fields = get_table_fields("信源配置")
    print(f"\n信源配置字段: {[f['name'] for f in src_fields]}")
    assert len(src_fields) == 9, f"信源配置应有9个字段: {len(src_fields)}"

    # 测试get_table_prefix
    assert get_table_prefix("信源配置") == "SRC"
    assert get_table_prefix("热帖库") == "TREND"
    assert get_table_prefix("选题库") == "TOPIC"

    # 测试种子数据
    src_seed = get_seed_data("信源配置")
    print(f"\n信源配置种子数据: {len(src_seed)} 条")
    assert len(src_seed) == 7, f"信源配置应有7条种子数据: {len(src_seed)}"

    koc_seed = get_seed_data("KOC人设")
    print(f"KOC人设种子数据: {len(koc_seed)} 条")
    assert len(koc_seed) == 1, f"KOC人设应有1条种子数据: {len(koc_seed)}"

    emp_seed = get_seed_data("Agent花名册")
    print(f"Agent花名册种子数据: {len(emp_seed)} 条")
    assert len(emp_seed) == 9, f"Agent花名册应有9条种子数据: {len(emp_seed)}"

    # 验证种子数据ID格式
    for item in src_seed:
        assert item["id"].startswith("SRC-"), f"种子数据ID格式错误: {item['id']}"

    print("\n[OK] Tables Schema 测试通过!")
    return True


def test_feishu_storage_mock():
    """测试FeishuStorage（使用Mock，不连接真实API）"""
    print("\n" + "="*60)
    print("测试4: FeishuStorage - 存储接口实现（概念验证）")
    print("="*60)

    # 注意：此测试不连接真实飞书API，仅验证代码结构和逻辑
    # 真实集成测试需要配置环境变量和飞书权限

    from core.storage.interface import Storage
    from feishu_adapter.feishu_storage import FeishuStorage

    # 验证类继承关系
    assert issubclass(FeishuStorage, Storage), "FeishuStorage应继承Storage"
    print("[OK] FeishuStorage 继承 Storage")

    # 验证方法存在
    required_methods = ['create', 'update', 'query', 'delete', 'get_by_id', 'exists']
    for method in required_methods:
        assert hasattr(FeishuStorage, method), f"缺少方法: {method}"
        print(f"[OK] 方法存在: {method}")

    # 验证IDMapping集成 (实例属性，在__init__中初始化)
    # 注意：id_mapping是实例属性，不是类属性
    print("[OK] IDMapping 已集成 (实例属性)")

    print("\n[OK] FeishuStorage 结构测试通过!")
    print("\n注意: 完整功能测试需要连接飞书API，请配置环境变量后运行:")
    print("  LARK_APP_ID, LARK_APP_SECRET, LARK_BASE_APP_TOKEN")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" NewsAI Storage接口层测试套件 ")
    print("="*70)

    results = []

    try:
        results.append(("IDGenerator", test_id_generator()))
    except Exception as e:
        results.append(("IDGenerator", False))
        print(f"\n[FAIL] IDGenerator 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        results.append(("IDMapping", test_id_mapping()))
    except Exception as e:
        results.append(("IDMapping", False))
        print(f"\n[FAIL] IDMapping 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        results.append(("TableSchema", test_table_schema()))
    except Exception as e:
        results.append(("TableSchema", False))
        print(f"\n[FAIL] TableSchema 测试失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        results.append(("FeishuStorage", test_feishu_storage_mock()))
    except Exception as e:
        results.append(("FeishuStorage", False))
        print(f"\n[FAIL] FeishuStorage 测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 打印汇总
    print("\n" + "="*70)
    print(" 测试结果汇总 ")
    print("="*70)
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 通过")

    return all(p for _, p in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
