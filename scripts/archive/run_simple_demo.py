#!/usr/bin/env python3
"""
简化版演示 - 只生成文档链接
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from datetime import datetime
import json


def run_simple_demo():
    """运行简化演示"""
    print("=" * 70)
    print("NewsAI 简化演示 - 生成文档链接")
    print("=" * 70)

    # 初始化
    print("\n[初始化]")
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    print("  [OK] 存储初始化完成")

    # 找一个选题
    print("\n[1/3] 查找选题...")
    all_topics = storage.query("选题库", limit=100)
    pending_topics = [t for t in all_topics if t.data.get("状态") == "已选"]

    if not pending_topics:
        print("  [错误] 没有找到状态为'已选'的选题")
        return

    topic = pending_topics[-1].data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "未命名选题")

    print(f"  [OK] 选中选题: {topic_title}")
    print(f"  [OK] 选题ID: {topic_id}")

    # ========== 小文 - 创建帖子文档 ==========
    print("\n[2/3] 小文 - 创建帖子文档...")

    date_str = datetime.now().strftime("%Y%m%d")

    # 创建帖子文档
    post_doc_id = doc_storage.create_post_doc(topic_title, date_str)
    print(f"  [OK] 帖子文档创建成功, ID: {post_doc_id}")

    # 构建简单内容（避免格式问题）
    post_content = f"""这是 {topic_title} 的帖子文档

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

公众号版本:
标题: AI效率革命：这款大模型让工作速度翻倍
摘要: 揭秘最新AI技术突破
正文: （此处为公众号正文内容，约1500字）
配图: 科技感封面图

小红书版本:
标题: 这款AI让我的效率翻倍！
正文: （此处为小红书正文内容，约300字）
标签: #AI工具 #效率神器

抖音版本:
文案: （此处为抖音文案，约100字）
钩子: 效率翻倍的关键
CTA: 评论区告诉我

B站版本:
标题: 【实测】最新大模型效率翻倍？
简介: 本期深度测试AI大模型工具
正文: （此处为B站专栏内容，约2000字）
"""

    # 追加内容（分段追加避免错误）
    try:
        doc_storage.append_section(post_doc_id, post_content)
        print(f"  [OK] 帖子内容已写入")
    except Exception as e:
        print(f"  [警告] 写入内容失败: {e}")
        # 尝试写入简化内容
        simple_content = f"文档标题: {topic_title}\n\n这是简化版内容。"
        doc_storage.append_section(post_doc_id, simple_content)
        print(f"  [OK] 简化内容已写入")

    # 获取分享链接
    post_doc_url = doc_storage.get_share_url(post_doc_id)
    print(f"  [OK] 帖子文档链接: {post_doc_url}")

    # ========== 小审 - 创建审改文档 ==========
    print("\n[3/3] 小审 - 创建审改文档...")

    # 创建审改文档
    audit_doc_id = doc_storage.create_audit_doc(topic_title, date_str)
    print(f"  [OK] 审改文档创建成功, ID: {audit_doc_id}")

    # 构建审改内容
    audit_content = f"""{topic_title} - 审改记录

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

审查结论: 通过
严重度: 低
审查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

审查指标:
- 事实核查: 通过
- 风险词扫描: 通过
- 人设一致性: 通过
- 平台合规性: 通过

发现的问题:
- 无问题
"""

    # 追加内容
    try:
        doc_storage.append_section(audit_doc_id, audit_content)
        print(f"  [OK] 审改内容已写入")
    except Exception as e:
        print(f"  [警告] 写入内容失败: {e}")
        simple_audit = f"文档标题: {topic_title} - 审改记录\n\n审查结论: 通过"
        doc_storage.append_section(audit_doc_id, simple_audit)
        print(f"  [OK] 简化审改内容已写入")

    # 获取分享链接
    audit_doc_url = doc_storage.get_share_url(audit_doc_id)
    print(f"  [OK] 审改文档链接: {audit_doc_url}")

    # ========== 更新飞书表格 ==========
    print("\n[更新飞书表格]")

    # 配图方案
    visual_scheme = [
        {"配图编号": "配图1", "用途": "封面", "类型": "文字卡片", "描述": "科技感背景"},
        {"配图编号": "配图2", "用途": "正文", "类型": "信息图", "描述": "效率对比图"},
        {"配图编号": "配图3", "用途": "正文", "类型": "AI画面", "描述": "AI大脑图"}
    ]

    update_data = {
        "帖子文档链接": post_doc_url,
        "审改文档链接": audit_doc_url,
        "配图方案": json.dumps(visual_scheme, ensure_ascii=False),
        "视觉风格": "简洁科技风",
        "审改轮次": 1,
        "状态": "待发布",
        "帖子内容": "（已写入飞书文档）",
        "审查通过时间": int(datetime.now().timestamp() * 1000)
    }

    try:
        storage.update("选题库", topic_id, update_data)
        print(f"  [OK] 选题库更新请求已发送")
    except Exception as e:
        print(f"  [ERROR] 选题库更新失败: {e}")
        import traceback
        traceback.print_exc()

    # 等待一下确保数据同步
    print("\n[等待数据同步...]")
    import time
    time.sleep(2)

    # 最终结果展示
    print("\n" + "=" * 70)
    print("生产完成 - 最终结果")
    print("=" * 70)

    final_topic = storage.get_by_id("选题库", topic_id)
    print(f"[调试] 读取到的记录: {final_topic}")
    if final_topic:
        data = final_topic.data
        print(f"\n选题标题: {data.get('选题标题', 'N/A')}")
        print(f"选题状态: {data.get('状态', 'N/A')}")
        print()
        print("【文档链接】字段:")

        post_url = data.get('帖子文档链接', '')
        audit_url = data.get('审改文档链接', '')

        # 处理URL格式（可能是字符串或字典）
        post_url_str = ''
        if post_url:
            if isinstance(post_url, dict):
                post_url_str = post_url.get('link', '')
            else:
                post_url_str = post_url

        audit_url_str = ''
        if audit_url:
            if isinstance(audit_url, dict):
                audit_url_str = audit_url.get('link', '')
            else:
                audit_url_str = audit_url

        if post_url_str:
            print(f"  帖子文档链接: {post_url_str}")
        else:
            print(f"  帖子文档链接: (空)")

        if audit_url_str:
            print(f"  审改文档链接: {audit_url_str}")
        else:
            print(f"  审改文档链接: (空)")

        print(f"  配图方案: {'已生成' if data.get('配图方案') else '未生成'}")
        print(f"  审改轮次: {data.get('审改轮次', 0)}")

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n请检查飞书多维表格【选题库】中的文档链接字段")


if __name__ == "__main__":
    run_simple_demo()
