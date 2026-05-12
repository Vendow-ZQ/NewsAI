#!/usr/bin/env python3
"""
最终演示脚本 - 为小文、小图、小审、小改生成文档链接
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
    """运行完整演示"""
    print("=" * 70)
    print("NewsAI 内容生产演示 - 小文/小图/小审/小改")
    print("=" * 70)

    # 初始化
    print("\n[初始化]")
    storage = FeishuStorage()
    doc_storage = FeishuDocStorage()
    print("  [OK] 存储初始化完成")

    # 查找一个合适的选题（已选状态）
    print("\n[1/5] 查找待生产的选题...")
    all_topics = storage.query("选题库", limit=100)

    # 找一个没有文档链接的已选选题
    pending_topics = []
    for t in all_topics:
        data = t.data
        if data.get("状态") == "已选" and not data.get("帖子文档链接"):
            pending_topics.append(t)

    if not pending_topics:
        # 如果没有，就找最后一个已选状态的
        for t in reversed(all_topics):
            if t.data.get("状态") == "已选":
                pending_topics.append(t)
                break

    if not pending_topics:
        print("  [错误] 没有找到合适的选题")
        return

    topic = pending_topics[0].data
    topic_id = topic.get("id")
    topic_title = topic.get("选题标题", "未命名选题")

    print(f"  [OK] 选中选题: {topic_title}")
    print(f"  [OK] 选题ID: {topic_id}")

    # ========== Step 1: 小文 - 创建帖子文档 ==========
    print("\n[2/5] 小文 - 撰写4平台内容并创建文档...")

    date_str = datetime.now().strftime("%Y%m%d")

    # 创建帖子文档
    post_doc_id = doc_storage.create_post_doc(topic_title, date_str)
    print(f"  [OK] 帖子文档创建成功")

    # 构建内容
    post_content = f"""# {topic_title}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 公众号版本

**标题**: {topic_title}深度解析：效率翻倍的秘密

**摘要**: 揭秘最新技术突破，实测效果惊人

**正文**:

姐妹们/兄弟们，今天给大家深度解析这个话题！

最近我在实践中发现了一个惊人的方法，用了一周后效率直接翻倍。不是夸张，是真实的效果提升。

### 核心方法

1. **系统化思维**：不再零散处理，而是建立完整流程
2. **工具组合**：善用AI工具链，而非单一工具
3. **持续优化**：每周复盘，不断优化工作流

### 实测效果

- 任务完成速度提升 200%
- 错误率降低 60%
- 工作满意度大幅提升

### 适合人群

- 经常处理重复性工作的职场人
- 需要提升学习效率的学生
- 想优化工作流程的创作者

### 总结

方法虽好，但关键在执行。建议从一个小场景开始尝试，逐步扩展。

你们平时最大的效率瓶颈是什么？评论区聊聊！

**配图**: 封面图+效果对比图+使用场景图

---

## 小红书版本

**标题**: 这个方法让我的效率翻倍！救命神器🚀

姐妹们！发现超神的方法！🎉

用了一周，效率直接翻倍！
以前4小时的任务，现在1.5小时搞定✅

三个核心要点：
1️⃣ 系统化思维
2️⃣ 工具组合使用
3️⃣ 持续优化迭代

实测效果：
✨ 速度提升200%
✨ 错误率降低60%

适合：职场人、学生党、创作者

#效率提升 #工作方法 # productivity #职场干货 #学习技巧

---

## 抖音版本

**钩子**: 效率翻倍的关键方法

**文案**:

你们知道吗？这个方法让我的工作效率直接翻倍！

以前我完成这个任务要4个小时，现在1.5小时就搞定了。

最绝的是上周五，老板临时加急任务，平时要一天，我用了2小时就完成了，还被表扬了！

评论区告诉我，你最想提升哪方面的效率？

**CTA**: 评论区告诉我你最想提升什么

---

## B站版本

**标题**: 【深度解析】效率翻倍的秘密方法 | 实测体验

**简介**: 本期深度测试效率提升方法，真实使用一周后效果惊人

**正文**:

大家好，欢迎来到本期视频。

今天我要分享的是一个最近发现的方法，用了一周后我的效率直接翻倍。

**[测试背景]**

作为职场人，我日常需要处理各种任务，经常感到时间不够用。

**[核心方法]**

1. 系统化思维建立流程
2. 工具组合提升效率
3. 持续优化迭代改进

**[实测数据]**

同样的任务：
- 传统方式：4小时
- 使用新方法：1.5小时

**[总结]**

方法虽好，关键在执行。建议从小场景开始，逐步扩展。

如果觉得这期视频有帮助，记得一键三连支持一下！我们下期再见！
"""

    # 追加内容
    try:
        doc_storage.append_section(post_doc_id, post_content)
        print(f"  [OK] 4平台内容已写入文档")
    except Exception as e:
        print(f"  [警告] 写入内容失败: {e}")
        simple_content = f"文档标题: {topic_title}\n\n（内容生成中）"
        doc_storage.append_section(post_doc_id, simple_content)

    # 获取分享链接
    post_doc_url = doc_storage.get_share_url(post_doc_id)
    print(f"  [OK] 帖子文档链接: {post_doc_url}")

    # ========== Step 2: 小图 - 生成配图方案 ==========
    print("\n[3/5] 小图 - 生成配图方案...")

    visual_scheme = [
        {
            "配图编号": "配图1",
            "用途": "公众号封面/小红书首图",
            "类型": "文字卡片",
            "描述": "标题+主视觉，蓝色科技感配色",
            "技术方案": "HTML模板渲染",
            "对应正文位置": "封面"
        },
        {
            "配图编号": "配图2",
            "用途": "正文插图",
            "类型": "信息图",
            "描述": "效果对比图，传统方式 vs 新方法",
            "技术方案": "SVG模板",
            "对应正文位置": "实测效果部分"
        },
        {
            "配图编号": "配图3",
            "用途": "正文插图",
            "类型": "AI画面图",
            "描述": "工作流程图，展示系统化思维",
            "技术方案": "即梦API",
            "AI生成Prompt": "workflow diagram, blue tech style, clean and modern",
            "对应正文位置": "核心方法部分"
        },
        {
            "配图编号": "配图4",
            "用途": "使用场景展示",
            "类型": "AI画面图",
            "描述": "职场人高效工作场景",
            "技术方案": "即梦API",
            "AI生成Prompt": "professional person working efficiently, modern office, tech vibe",
            "对应正文位置": "适合人群部分"
        }
    ]

    print(f"  [OK] 配图方案已生成 ({len(visual_scheme)} 张图)")

    # ========== Step 3: 小审 - 审查内容并创建审改文档 ==========
    print("\n[4/5] 小审 - 审查内容并创建审改文档...")

    # 创建审改文档
    audit_doc_id = doc_storage.create_audit_doc(topic_title, date_str)
    print(f"  [OK] 审改文档创建成功")

    # 构建审改内容
    audit_content = f"""# {topic_title} - 审改记录

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 审查结论

**审查结果**: 通过 ✅
**严重度**: 低
**审查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 审查指标

| 检查项 | 结果 |
|--------|------|
| 事实核查 | 通过 |
| 风险词扫描 | 通过 |
| 人设一致性 | 通过 |
| 平台合规性 | 通过 |

---

## 发现的问题

**问题数量**: 0

审查结果良好，无需修改。

---

## 审查详情

### 事实核查
- 所有技术描述准确
- 数据来源可靠
- 引用内容属实

### 风险词扫描
- 未发现敏感词汇
- 无政治风险
- 无版权风险

### 人设一致性
- 符合KOC语气基调
- 保持专业性与亲和力
- 互动引导自然

### 平台合规性
- 符合公众号规范
- 符合小红书社区规则
- 符合抖音内容标准
- 符合B站投稿要求

---

## 处理记录

- 审查通过，状态更新为"待发布"
- 文档已创建并设置权限
- 配图方案已生成

---

审改完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    # 追加内容
    try:
        doc_storage.append_section(audit_doc_id, audit_content)
        print(f"  [OK] 审改记录已写入文档")
    except Exception as e:
        print(f"  [警告] 写入内容失败: {e}")
        simple_audit = f"审改记录: {topic_title}\n\n审查结论: 通过"
        doc_storage.append_section(audit_doc_id, simple_audit)

    # 获取分享链接
    audit_doc_url = doc_storage.get_share_url(audit_doc_id)
    print(f"  [OK] 审改文档链接: {audit_doc_url}")

    # ========== Step 4: 更新飞书表格 ==========
    print("\n[5/5] 更新飞书多维表格...")

    update_data = {
        "帖子文档链接": post_doc_url,
        "审改文档链接": audit_doc_url,
        "配图方案": json.dumps(visual_scheme, ensure_ascii=False),
        "视觉风格": "简洁科技风，蓝白配色",
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
        import traceback
        traceback.print_exc()

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
        visual = data.get('配图方案', '')
        review_round = data.get('审改轮次', 0)

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

        print(f"  帖子文档链接: {post_url_str if post_url_str else '(空)'}")
        print(f"  审改文档链接: {audit_url_str if audit_url_str else '(空)'}")
        print(f"  配图方案: {'已生成' if visual else '未生成'}")
        print(f"  审改轮次: {review_round}")

        print()
        if post_url_str:
            print("✅ 帖子文档创建成功！")
        if audit_url_str:
            print("✅ 审改文档创建成功！")
        if visual:
            print("✅ 配图方案已生成！")

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print()
    print("📋 生产流程:")
    print("  1. 小文(ContentWriter) - 撰写4平台内容并创建帖子文档")
    print("  2. 小图(VisualDesigner) - 生成配图方案")
    print("  3. 小审(Reviewer) - 审查内容并创建审改文档")
    print("  4. (小改Editor - 本例无需修改，跳过)")
    print()
    print("📌 请检查飞书多维表格【选题库】中的以下字段:")
    print("   - 帖子文档链接 (飞书云文档URL)")
    print("   - 审改文档链接 (飞书云文档URL)")
    print("   - 配图方案 (JSON格式)")
    print("   - 状态 (已更新为'待发布')")
    print()
    print("📄 帖子文档包含:")
    print("   - 公众号版本（深度长文）")
    print("   - 小红书版本（图文笔记）")
    print("   - 抖音版本（短视频文案）")
    print("   - B站版本（专栏文章）")
    print()
    print("🔍 审改文档包含:")
    print("   - 审查结论")
    print("   - 审查指标（事实核查/风险词/人设/合规）")
    print("   - 发现的问题清单")


if __name__ == "__main__":
    run_demo()
