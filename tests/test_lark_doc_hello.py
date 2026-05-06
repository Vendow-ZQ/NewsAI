"""飞书云文档 SDK Hello World 测试（v2 基础设施验证）。

验证：
1. 创建空白 Docx（通过 FeishuDocStorage）
2. 写入 markdown 内容（H1/H2/H3、段落、列表、代码块）
3. 获取分享链接（URL 含 docx，非 tbl）
4. print URL 确认成功
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from feishu_adapter.docs.folder_manager import FolderManager


def main():
    print("=" * 60)
    print("飞书云文档 Hello World 测试 (v2 基础设施)")
    print("=" * 60)

    # 1. 初始化
    doc_storage = FeishuDocStorage()
    folder_mgr = FolderManager()

    # 2. 确保文件夹存在（若应用无 drive 权限则跳过）
    print("\n[1/5] 确保 NewsAI产物 文件夹...")
    try:
        folders = folder_mgr.ensure_newsai_folders()
        print(f"文件夹 tokens: {list(folders.keys())}")
        posts_folder = folders.get("帖子")
    except Exception as e:
        print(f"[WARN] 文件夹创建跳过: {e}")
        folders = {}
        posts_folder = None

    # 3. 创建测试文档
    print("\n[2/5] 创建测试文档...")
    doc_id = doc_storage.create_doc("[测试] Hello World 云文档", folder_token=posts_folder)
    print(f"文档 ID: {doc_id}")

    # 4. 写入 markdown 内容
    print("\n[3/5] 写入 markdown 内容...")
    markdown = """# Hello World 测试文档

这是 NewsAI 云文档架构的验证文档。

---

## 二级标题示例

这是一段普通段落，支持 **粗体**、*斜体* 和 `行内代码`。

### 三级标题示例

无序列表：
- 列表项 A
- 列表项 B
- 列表项 C

有序列表：
1. 第一步
2. 第二步
3. 第三步

代码块：
```python
def hello():
    print("Hello, Feishu Docx!")
```

引用块：
> 这是一段引用文字。

---

**测试完成时间**：2026-05-05
"""
    doc_storage.append_section(doc_id, markdown)
    print("Markdown 内容已写入")

    # 5. 设置权限并获取链接
    print("\n[4/5] 设置权限...")
    try:
        doc_storage.set_permissions(doc_id, share_type="tenant_editable")
    except Exception as e:
        print(f"[WARN] 权限设置跳过: {e}")

    print("\n[5/5] 获取分享链接...")
    url = doc_storage.get_share_url(doc_id)
    print(f"分享链接: {url}")

    # 验证 URL 含 docx（飞书 Docx 链接特征）
    assert "docx" in url, f"URL 格式异常: {url}"

    print("\n" + "=" * 60)
    print("[PASS] 测试通过！请用浏览器打开上方链接验证格式。")
    print("=" * 60)

    return url


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
