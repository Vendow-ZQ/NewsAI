"""清理选题库中的重复记录。

保留每个ID的最新记录（有URL字段的），删除旧的重复记录。
"""
import os
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure env is loaded
from dotenv import load_dotenv
load_dotenv()

from core.utils.feishu_base import FeishuBaseManager


def cleanup_topic_duplicates():
    """清理选题库重复记录。"""
    base = FeishuBaseManager()
    tables = base.list_tables(use_cache=False)
    table_id = tables.get('选题库')

    if not table_id:
        print("[错误] 找不到选题库表")
        return

    print(f"[INFO] 选题库表ID: {table_id}")

    # 获取所有记录
    records = base.list_records(table_id)
    print(f"[INFO] 总记录数: {len(records)}")

    # 按ID分组
    by_id = defaultdict(list)
    for r in records:
        fields = r.get('fields', {})
        rec_id = fields.get('id')
        if rec_id:
            by_id[rec_id].append(r)

    # 找出重复的记录
    duplicates = {k: v for k, v in by_id.items() if len(v) > 1}
    print(f"[INFO] 重复ID数量: {len(duplicates)}")

    if not duplicates:
        print("[INFO] 没有重复记录，无需清理")
        return

    # 对每个重复组，保留有URL的记录，删除其他的
    deleted = 0
    for rec_id, recs in duplicates.items():
        print(f"\n[ID: {rec_id}] 有 {len(recs)} 条重复记录")

        # 优先保留有帖子文档链接的记录
        best = None
        for r in recs:
            fields = r.get('fields', {})
            if fields.get('帖子文档链接'):
                best = r
                break

        # 如果没有URL，保留第一个
        if not best:
            best = recs[0]

        print(f"  保留: record_id={best.get('record_id')}")

        # 删除其他的
        for r in recs:
            if r.get('record_id') != best.get('record_id'):
                try:
                    base.delete_record(table_id, r.get('record_id'))
                    print(f"  删除: record_id={r.get('record_id')}")
                    deleted += 1
                except Exception as e:
                    print(f"  删除失败: {e}")

    print(f"\n[完成] 删除了 {deleted} 条重复记录")


if __name__ == "__main__":
    cleanup_topic_duplicates()
