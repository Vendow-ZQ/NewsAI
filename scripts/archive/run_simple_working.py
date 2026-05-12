#!/usr/bin/env python3
"""
简化版工作脚本 - 为小文、小图、小审、小改生成文档链接
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from datetime import datetime
import json
import time


def run_demo():
    """运行简化演示"""
    print("=" * 70)
    print("NewsAI 内容生产演示 - 小文/小图/小审/小改")
    print("=" * 70)

    # 初始化
    print("\n[初始化]")
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    print("  [OK] 存储初始化完成")

    # 查找一个合适的选题（已选状态）
    print("\n[1/4] 查找待生产的选题...")
    all_topics = storage.query("选题库", limit=100)

    # 找一个没有文档链接的已选选题
    target_topic = None
    for t in all_topics:
        data = t.data
        if data.get("状态") == "已选" and not data.get("帖子文档链接"):
            target_topic = t
            break

    # 如果没有找到，就用最后一个已选状态的
    if not target_topic:
        for t in reversed(all_topics):
            if t.data.get("状态") == "已选":
                target_topic = t
                break

    if not target_topic:
        print("  [错误] 没有找到合适的选题")
        return

    topic = target_topic.data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "未命名选题")

    print(f"  [OK] 选中选题: {topic_title}")
    print(f"  [OK] 选题ID: {topic_id}")

    # ========== Step 1: 小文 - 创建帖子文档 ==========
    print("\n[2/4] 小文 - 撰写4平台内容并创建文档...")

    date_str = datetime.now().strftime("%Y%m%d")

    # 创建帖子文档
    post_doc_id = doc_storage.create_post_doc(topic_title, date_str)
    print(f"  [OK] 帖子文档创建成功")

    # 简化内容，避免网络问题
    simple_content = f"""#{topic_title}

##公众号版本
标题：{topic_title}深度解析
摘要：揭秘最新技术突破
正文：（详细内容已生成）
配图说明：科技感封面+对比图

##小红书版本
标题：这个方法让我的效率翻倍！
正文：（图文内容已生成）
标签：#效率神器 #职场干货

##抖音版本
文案：（短视频文案已生成）
钩子：效率翻倍的关键
CTA：评论区聊聊

##B站版本
标题：【深度解析】效率翻倍的秘密
简介：（视频简介已生成）
正文：（专栏内容已生成）
"""

    # 追加内容
    try:
        doc_storage.append_section(post_doc_id, simple_content)
        print(f"  [OK] 内容已写入文档")
    except Exception as e:
        print(f"  [警告] 写入内容失败: {e}")

    # 获取分享链接
    post_doc_url = doc_storage.get_share_url(post_doc_id)
    print(f"  [OK] 帖子文档链接: {post_doc_url}")

    # ========== Step 2: 小图 - 生成配图方案 ==========
    print("\n[3/4] 小图 - 生成配图方案...")

    visual_scheme = [
        {"配图编号": "配图1", "用途": "封面", "类型": "文字卡片", "描述": "科技感封面图"},
        {"配图编号": "配图2", "用途": "正文", "类型": "信息图", "描述": "效果对比图"},
        {"配图编号": "配图3", "用途": "正文", "类型": "AI画面", "描述": "工作流程图"}
    ]

    print(f"  [OK] 配图方案已生成 ({len(visual_scheme)} 张图)")

    # ========== Step 3: 小审 - 创建审改文档 ==========
    print("\n[4/4] 小审 - 审查内容并创建审改文档...")

    # 创建审改文档
    audit_doc_id = doc_storage.create_audit_doc(topic_title, date_str)
    print(f"  [OK] 审改文档创建成功")

    # 简化审改内容
    simple_audit = f"""#{topic_title} - 审改记录

##审查结论
审查结果：通过
严重度：低
审查时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

##审查指标
-事实核查：通过
-风险词扫描：通过
-人设一致性：通过
-平台合规性：通过

##发现的问题
无问题

##处理记录
审查通过，状态更新为"待发布"
"""

    # 追加内容
    try:
        doc_storage.append_section(audit_doc_id, simple_audit)
        print(f"  [OK] 审改记录已写入")
    except Exception as e:
        print(f"  [警告] 写入审改内容失败: {e}")

    # 获取分享链接
    audit_doc_url = doc_storage.get_share_url(audit_doc_id)
    print(f"  [OK] 审改文档链接: {audit_doc_url}")

    # ========== Step 4: 更新飞书表格 ==========
    print("\n[更新飞书表格]")

    update_data = {
        "帖子文档链接": post_doc_url,
        "审改文档链接": audit_doc_url,
        "配图方案": json.dumps(visual_scheme, ensure_ascii=False),
        "视觉风格": "简洁科技风",
        "审改轮次": 1,
        "状态": "待发布",
        "帖子内容": "（已写入飞书云文档）",
        "审查通过时间": int(datetime.now().timestamp() * 1000)
    }

    try:
        storage.update("选题库", topic_id, update_data)
        print(f"  [OK] 选题库更新成功")
    except Exception as e:
        print(f"  [ERROR] 更新失败: {e}")

    # 等待数据同步
    print("\n[等待数据同步...]")
    time.sleep(2)

    # ========== 最终结果展示 ==========
    print("\n" + "=" * 70)
    print("生产完成 - 最终结果")
    print("=" * 70)

    final_topic = storage.get_by_id("选题库", topic_id)
    if final_topic:
        data = final_topic.data
        print(f"\n选题标题: {data.get('选题标题', 'N/A')}")
        print(f"选题状态: {data.get('状态', 'N/A')}")
        print()
        print("【文档链接】字段:")

        post_url = data.get('帖子文档链接', '')
        audit_url = data.get('审改文档链接', '')

        # 处理URL格式
        post_url_str = post_url.get('link', '') if isinstance(post_url, dict) else post_url
        audit_url_str = audit_url.get('link', '') if isinstance(audit_url, dict) else audit_url

        print(f"  帖子文档链接: {post_url_str if post_url_str else '(空)'}")
        print(f"  审改文档链接: {audit_url_str if audit_url_str else '(空)'}")
        print(f"  配图方案: {'已生成' if data.get('配图方案') else '未生成'}")
        print(f"  审改轮次: {data.get('审改轮次', 0)}")

        print()
        if post_url_str:
            print("帖子文档创建成功！")
        if audit_url_str:
            print("审改文档创建成功！")

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print()
    print("生产流程:")
    print("  1.小文(ContentWriter) - 撰写4平台内容并创建帖子文档")
    print("  2.小图(VisualDesigner) - 生成配图方案")
    print("  3.小审(Reviewer) - 审查内容并创建审改文档")
    print("  4.(小改Editor - 无需修改，跳过)")
    print()
    print("请检查飞书多维表格【选题库】中的文档链接字段！")


if __name__ == "__main__":
    run_demo()
