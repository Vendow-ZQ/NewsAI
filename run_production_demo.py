#!/usr/bin/env python3
"""
内容生产演示 - 小文、小图、小审、小改
生成真实的文档链接并写入飞书多维表格
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
from datetime import datetime


def create_post_document(doc_storage, topic_title, platforms_content):
    """创建帖子文档"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 创建文档
    doc_id = doc_storage.create_post_doc(topic_title, date_str)

    # 构建内容（简化版，避免格式问题）
    content = f"# {topic_title}\n\n"
    content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # 公众号版本
    gzh = platforms_content['公众号']
    content += "## 公众号版本\n\n"
    content += f"标题: {gzh['标题']}\n\n"
    content += f"摘要: {gzh['摘要']}\n\n"
    content += f"正文:\n{gzh['正文']}\n\n"
    content += f"配图: {gzh['配图说明']}\n\n"

    # 小红书版本
    xhs = platforms_content['小红书']
    content += "## 小红书版本\n\n"
    content += f"标题: {xhs['标题']}\n\n"
    content += f"正文:\n{xhs['正文']}\n\n"
    content += f"标签: {xhs['标签']}\n\n"

    # 抖音版本
    dy = platforms_content['抖音']
    content += "## 抖音版本\n\n"
    content += f"钩子: {dy['钩子']}\n\n"
    content += f"文案:\n{dy['文案']}\n\n"
    content += f"CTA: {dy['CTA']}\n\n"

    # B站版本
    bz = platforms_content['B站']
    content += "## B站版本\n\n"
    content += f"标题: {bz['标题']}\n\n"
    content += f"简介: {bz['简介']}\n\n"
    content += f"正文:\n{bz['正文']}\n\n"

    # 追加到文档
    doc_storage.append_section(doc_id, content)

    # 设置权限
    try:
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
    except Exception as e:
        print(f"    [警告] 设置权限失败: {e}")

    # 获取分享链接
    share_url = doc_storage.get_share_url(doc_id)

    return doc_id, share_url


def create_audit_document(doc_storage, topic_title, review_data):
    """创建审改文档"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 创建文档
    doc_id = doc_storage.create_audit_doc(topic_title, date_str)

    # 构建内容
    content = f"# {topic_title} - 审改记录\n\n"
    content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # 审查结论
    content += "## 审查结论\n\n"
    content += f"**结论**: {review_data['conclusion']}\n\n"
    content += f"**严重度**: {review_data['severity']}\n\n"
    content += f"**审查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # 审查指标
    content += "### 审查指标\n\n"
    for metric, value in review_data['metrics'].items():
        content += f"- {metric}: {value}\n"
    content += "\n"

    # 发现的问题
    content += "### 发现的问题\n\n"
    if review_data['issues']:
        for issue in review_data['issues']:
            content += f"- **{issue['location']}**: {issue['problem']}\n"
            content += f"  - 建议: {issue['suggestion']}\n"
    else:
        content += "- 无问题\n"

    content += "\n"

    # 追加到文档
    doc_storage.append_section(doc_id, content)

    # 设置权限
    try:
        doc_storage.set_permissions(doc_id, share_type="tenant_readable")
    except Exception as e:
        print(f"    [警告] 设置权限失败: {e}")

    # 获取分享链接
    share_url = doc_storage.get_share_url(doc_id)

    return doc_id, share_url


def run_demo():
    """运行演示"""
    print("=" * 70)
    print("NewsAI 内容生产演示")
    print("=" * 70)

    # 初始化
    print("\n[初始化]")
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    print("  [OK] 存储初始化完成")

    # 找一个选题
    print("\n[1/4] 查找待生产的选题...")
    all_topics = storage.query("选题库", limit=100)
    pending_topics = [t for t in all_topics if t.data.get("状态") == "已选"]

    if not pending_topics:
        print("  [错误] 没有找到状态为'已选'的选题")
        print("  提示: 请先运行小编生成选题")
        return

    topic = pending_topics[-1].data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "未命名选题")

    print(f"  [OK] 选中选题: {topic_title}")
    print(f"  [OK] 选题ID: {topic_id}")

    # ========== 小文 - 内容撰写 ==========
    print("\n[2/4] 小文 - 撰写4平台内容...")

    # 模拟4平台内容
    platforms_content = {
        "公众号": {
            "标题": "AI效率革命：这款大模型让工作速度翻倍",
            "摘要": "揭秘最新AI技术突破，实测效率提升200%",
            "正文": "姐妹们/兄弟们，今天给大家安利一个超神的AI工具！\n\n"
                    "最近我在日常工作中发现了一个大模型，用了一周后效率直接翻倍。"
                    "不是夸张，是真实的效率提升。\n\n"
                    "## 效率对比实测\n\n"
                    "以前写一份报告需要4小时，现在只需要1.5小时。\n\n"
                    "以前整理数据需要半天，现在30分钟搞定。\n\n"
                    "## 核心功能\n\n"
                    "这个AI有三个让我惊艳的功能：\n\n"
                    "1. **智能理解上下文**：不像其他AI需要反复解释\n\n"
                    "2. **多任务并行处理**：同时处理文档、数据、代码\n\n"
                    "3. **自适应学习**：用越久越懂你的工作习惯\n\n"
                    "## 使用建议\n\n"
                    "刚开始用建议从简单任务入手，慢慢熟悉交互方式。\n\n"
                    "## 总结\n\n"
                    "AI不是要替代我们，而是让我们从重复劳动中解放出来。\n\n"
                    "你们平时在工作中最大的效率瓶颈是什么？评论区聊聊！",
            "配图说明": "科技感封面图+效率对比示意图"
        },
        "小红书": {
            "标题": "这款AI让我的效率翻倍！打工人救命神器",
            "正文": "姐妹们！发现一款超神的AI工具！🚀\n\n"
                    "用了一周，效率直接翻倍！\n"
                    "以前4小时的报告，现在1.5小时搞定✅\n\n"
                    "三个核心功能：\n"
                    "1️⃣ 智能理解上下文\n"
                    "2️⃣ 多任务并行处理\n"
                    "3️⃣ 自适应学习\n\n"
                    "上周五2小时完成竞品分析，还被老板表扬了！\n\n"
                    "适合：职场人、分析师、学生党\n\n"
                    "打工人必备！",
            "标签": "#AI工具 #效率神器 #打工人必备 #职场干货"
        },
        "抖音": {
            "文案": "你们知道吗？最新的AI大模型让我的工作效率直接翻倍！\n\n"
                    "以前我写一份报告要4个小时，现在1.5小时就搞定了。\n\n"
                    "最绝的是上周五，老板临时要竞品分析，平时要一天的任务，"
                    "我用了2小时就完成了，还被表扬了！\n\n"
                    "评论区告诉我，你最想用AI提升哪方面的效率？",
            "钩子": "效率翻倍的关键就在这个设置",
            "CTA": "评论区告诉我你最想用AI做什么"
        },
        "B站": {
            "标题": "【实测】最新大模型效率翻倍？打工人真实使用体验",
            "简介": "本期深度测试一款AI大模型工具，真实使用一周后效率提升200%",
            "正文": "大家好，欢迎来到本期视频。\n\n"
                    "今天我要分享的是一款最近发现的AI大模型，用了一周后我的工作效率直接翻倍。\n\n"
                    "【测试背景】\n\n"
                    "作为打工人，我日常需要写报告、做PPT、整理数据...\n\n"
                    "【效率对比】\n\n"
                    "同样的报告任务：\n"
                    "- 传统方式：4小时\n"
                    "- 使用AI辅助：1.5小时\n\n"
                    "【核心功能】\n\n"
                    "1. 智能理解上下文\n"
                    "2. 多任务并行处理\n"
                    "3. 自适应学习\n\n"
                    "【总结】\n\n"
                    "AI不是要替代我们，而是让我们从重复劳动中解放出来。\n\n"
                    "如果觉得这期视频有帮助，记得一键三连支持一下！"
        }
    }

    # 创建文档
    doc_id, doc_url = create_post_document(doc_storage, topic_title, platforms_content)
    print(f"  [OK] 帖子文档创建成功")
    print(f"  [OK] 文档链接: {doc_url}")

    # 更新选题库
    storage.update("选题库", topic_id, {
        "帖子文档链接": doc_url,
        "帖子内容": platforms_content['公众号']['正文'][:500] + "...",
        "状态": "生产中"
    })
    print(f"  [OK] 选题库已更新")

    # ========== 小图 - 配图方案 ==========
    print("\n[3/4] 小图 - 生成配图方案...")

    visual_scheme = [
        {
            "配图编号": "配图1",
            "用途": "公众号封面/小红书首图",
            "类型": "文字卡片",
            "描述": "科技感背景+大标题'效率翻倍'，蓝色渐变配色",
            "技术方案": "HTML模板渲染",
            "对应正文位置": "封面"
        },
        {
            "配图编号": "配图2",
            "用途": "正文插图",
            "类型": "信息图",
            "描述": "效率对比柱状图，传统方式4小时 vs AI辅助1.5小时",
            "技术方案": "SVG模板",
            "对应正文位置": "效率对比实测"
        },
        {
            "配图编号": "配图3",
            "用途": "正文插图",
            "类型": "AI画面图",
            "描述": "AI大脑神经网络图，科技感蓝色光效",
            "技术方案": "即梦API",
            "AI生成Prompt": "futuristic AI brain, neural networks, blue glow, high tech",
            "对应正文位置": "核心功能解析"
        }
    ]

    import json
    storage.update("选题库", topic_id, {
        "配图方案": json.dumps(visual_scheme, ensure_ascii=False),
        "视觉风格": "简洁科技风，蓝白配色为主"
    })
    print(f"  [OK] 配图方案已生成 ({len(visual_scheme)} 张图)")

    # ========== 小审 - 内容审查 ==========
    print("\n[4/4] 小审 - 审查内容...")

    review_data = {
        "conclusion": "通过",
        "severity": "低",
        "metrics": {
            "事实核查": "通过",
            "风险词扫描": "通过",
            "人设一致性": "通过",
            "平台合规性": "通过"
        },
        "issues": []  # 没有问题
    }

    # 创建审改文档
    audit_doc_id, audit_doc_url = create_audit_document(doc_storage, topic_title, review_data)
    print(f"  [OK] 审改文档创建成功")
    print(f"  [OK] 文档链接: {audit_doc_url}")

    # 更新选题库
    storage.update("选题库", topic_id, {
        "审改文档链接": audit_doc_url,
        "审改轮次": 1,
        "状态": "待发布",
        "审查通过时间": int(datetime.now().timestamp() * 1000)
    })
    print(f"  [OK] 选题库已更新")

    # 最终结果展示
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

        if post_url:
            # 处理可能是字典的情况
            if isinstance(post_url, dict):
                post_url = post_url.get('link', '')
            print(f"  📄 帖子文档链接: {post_url}")
        else:
            print(f"  📄 帖子文档链接: (空)")

        if audit_url:
            # 处理可能是字典的情况
            if isinstance(audit_url, dict):
                audit_url = audit_url.get('link', '')
            print(f"  🔍 审改文档链接: {audit_url}")
        else:
            print(f"  🔍 审改文档链接: (空)")

        print(f"  🎨 配图方案: {'已生成' if data.get('配图方案') else '未生成'}")
        print(f"  📝 审改轮次: {data.get('审改轮次', 0)}")

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n📌 请检查飞书多维表格【选题库】中的以下字段:")
    print("   - 帖子文档链接 (应该包含飞书文档URL)")
    print("   - 审改文档链接 (应该包含飞书文档URL)")
    print("   - 配图方案 (应该包含JSON格式的配图方案)")
    print("   - 状态 (应该为'待发布')")


if __name__ == "__main__":
    run_demo()
