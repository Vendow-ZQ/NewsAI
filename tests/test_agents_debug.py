#!/usr/bin/env python3
"""调试脚本 - 测试小文、小图、小审、小改"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from datetime import datetime

def test_doc_creation():
    """测试文档创建功能"""
    print("=" * 60)
    print("测试飞书文档创建")
    print("=" * 60)

    try:
        doc_storage = FeishuDocStorage()
        print("[OK] FeishuDocStorage 初始化成功")

        # 测试创建文档
        date_str = datetime.now().strftime("%Y%m%d")
        test_title = "测试选题"

        print(f"\n创建帖子文档: {test_title}")
        doc_id = doc_storage.create_post_doc(test_title, date_str)
        print(f"[OK] 文档创建成功, doc_id: {doc_id}")

        # 测试追加内容
        test_content = """# 测试内容

这是测试内容。

## 小节标题

- 列表项1
- 列表项2

**粗体文字**
"""
        print("\n追加测试内容...")
        doc_storage.append_section(doc_id, test_content)
        print("[OK] 内容追加成功")

        # 测试设置权限
        print("\n设置文档权限...")
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
        print("[OK] 权限设置成功")

        # 测试获取分享链接
        share_url = doc_storage.get_share_url(doc_id)
        print(f"\n分享链接: {share_url}")

        print("\n" + "=" * 60)
        print("文档创建测试完成！")
        print("请检查上面的链接是否可以访问")
        print("=" * 60)

        return share_url

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_storage_update():
    """测试存储更新功能"""
    print("\n" + "=" * 60)
    print("测试存储更新")
    print("=" * 60)

    try:
        storage = FeishuStorage()
        print("[OK] FeishuStorage 初始化成功")

        # 找一个选题来测试更新
        all_topics = storage.query("选题库", limit=10)
        if not all_topics:
            print("[WARNING] 没有找到选题，跳过更新测试")
            return

        topic = all_topics[0]
        topic_id = topic.data.get("id")
        topic_title = topic.data.get("选题标题", "")

        print(f"\n选中选题: {topic_title}")
        print(f"选题ID: {topic_id}")

        # 测试更新帖子文档链接字段
        test_url = "https://f5tgebopkn.feishu.cn/docx/test123"
        print(f"\n更新帖子文档链接为: {test_url}")

        update_data = {
            "帖子文档链接": test_url,
            "状态": "生产中",
        }

        storage.update("选题库", topic_id, update_data)
        print("[OK] 更新成功")

        # 验证更新
        updated = storage.get_by_id("选题库", topic_id)
        saved_url = updated.data.get("帖子文档链接", "")
        print(f"\n验证 - 保存的链接: {saved_url}")

        if saved_url == test_url:
            print("[OK] 数据验证成功")
        else:
            print(f"[WARNING] 数据验证失败，期望: {test_url}, 实际: {saved_url}")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("NewsAI Agent 调试脚本")
    print("=" * 60)

    # 测试文档创建
    doc_url = test_doc_creation()

    # 测试存储更新
    test_storage_update()

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
