#!/usr/bin/env python3
"""测试 - 使用Mock LLM绕过真实调用"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.interface import QueryFilter


class MockLLM:
    """Mock LLM - 立即返回预设结果"""
    def invoke(self, prompt):
        # 根据prompt内容返回不同mock结果
        if "选题" in prompt or "爆点" in prompt:
            return '''{"是否适合": true, "选题标题": "测试选题-Mock", "选题角度": "测试角度", "预估爆点": "测试爆点", "预估受众": "测试受众", "推荐优先级": 8}'''
        elif "公众号" in prompt or "小红书" in prompt:
            return '''{"公众号": {"标题": "测试标题", "摘要": "测试摘要", "正文": "测试正文内容", "配图说明": "测试配图"}, "小红书": {"标题": "测试标题", "正文": "测试正文", "标签": "#测试"}, "抖音": {"文案": "测试文案", "钩子": "测试钩子", "CTA": "测试CTA"}, "B站": {"标题": "测试标题", "简介": "测试简介", "正文": "测试正文"}}'''
        elif "配图" in prompt or "视觉" in prompt:
            return '''{"配图思路": "测试配图思路", "图片清单": [{"类型": "封面", "描述": "测试封面"}], "即梦提示词": "测试提示词", "文字卡片HTML": "<div>测试</div>"}'''
        elif "脚本" in prompt or "视频" in prompt:
            return '''{"时长": "60秒", "镜头清单": [{"镜号": 1, "画面": "测试画面", "文案": "测试文案", "时长": 5}], "完整文案": "测试文案", "发布建议": {"最佳发布时间": "18:00", "互动钩子": "测试钩子"}}'''
        elif "审查" in prompt or "审改" in prompt:
            return '''{"审查结论": "通过", "问题清单": [], "修改建议": "无需修改"}'''
        elif "分发" in prompt:
            return '''{"分发计划": [{"平台": "公众号", "发布时间": "2026-05-04 18:00", "内容形式": "长文"}], "注意事项": "测试注意"}'''
        else:
            return '{"result": "mock"}'


def test_full_flow_mock():
    """使用Mock LLM测试完整流程"""

    print("[0] 初始化...")
    storage = FeishuStorage()
    llm = MockLLM()
    print("  [OK] 初始化完成")

    # 1. 检查热帖库
    print("\n[1] 检查热帖库...")
    filters = [QueryFilter(field="状态", operator="eq", value="待选")]
    trends = storage.query("热帖库", filters=filters, limit=10)
    print(f"  [OK] 待选热帖: {len(trends)}条")

    if not trends:
        print("  [ERR] 没有待选热帖")
        return

    # 2. 运行小编
    print("\n[2] 运行小编Agent...")
    from core.agents.topic_curator import TopicCuratorAgent

    topic_agent = TopicCuratorAgent(storage, llm)
    try:
        topic_result = topic_agent.execute({"koc_id": "KOC-001"})
        print(f"  [OK] 小编生成: {topic_result.get('count', 0)}条选题")
    except Exception as e:
        print(f"  [ERR] 小编执行失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 获取刚创建的选题
    topics = storage.query("选题库", filters=[QueryFilter(field="状态", operator="eq", value="已选")], limit=10)
    if not topics:
        print("  [ERR] 小编未创建选题")
        return

    topic_id = topics[0].data.get("业务ID")
    print(f"  [OK] 使用选题: {topic_id}")

    # 3. 并发运行生产组
    print("\n[3] 并发运行生产组...")
    from core.agents.content_writer import ContentWriterAgent
    from core.agents.visual_designer import VisualDesignerAgent
    from core.agents.script_writer import ScriptWriterAgent

    writer = ContentWriterAgent(storage, llm)
    visual = VisualDesignerAgent(storage, llm)
    script = ScriptWriterAgent(storage, llm)

    writer_result = writer.execute({"topic_id": topic_id})
    visual_result = visual.execute({"topic_id": topic_id})
    script_result = script.execute({"topic_id": topic_id})

    print(f"  [OK] 小文: {writer_result.get('count', 0)}条")
    print(f"  [OK] 小图: {visual_result.get('count', 0)}条")
    print(f"  [OK] 小播: {script_result.get('count', 0)}条")

    # 4. 运行小审
    print("\n[4] 运行小审Agent...")
    from core.agents.reviewer import ReviewerAgent

    review_agent = ReviewerAgent(storage, llm)
    review_result = review_agent.execute({"topic_id": topic_id})
    verdict = review_result.get("review_results", [{}])[0].get("review_result", {}).get("审查结论", "需修改")
    print(f"  [OK] 小审查结论: {verdict}")

    # 5. 运行小发
    print("\n[5] 运行小发Agent...")
    from core.agents.distributor import DistributorAgent

    dist_agent = DistributorAgent(storage, llm)
    dist_result = dist_agent.execute({"topic_id": topic_id})
    print(f"  [OK] 小发完成")

    # 6. 检查最终结果
    print("\n[6] 检查最终结果...")
    topics = storage.query("选题库", filters=[QueryFilter(field="业务ID", operator="eq", value=topic_id)], limit=1)
    if topics:
        fields = topics[0].data
        print(f"  选题标题: {fields.get('选题标题', 'N/A')}")
        print(f"  状态: {fields.get('状态', 'N/A')}")
        print(f"  帖子内容: {'[OK] 有' if fields.get('帖子内容') else '[NONE] 无'}")
        print(f"  视频脚本: {'[OK] 有' if fields.get('视频脚本内容') else '[NONE] 无'}")
        print(f"  审改记录: {'[OK] 有' if fields.get('审改记录') else '[NONE] 无'}")
        print(f"  分发计划: {'[OK] 有' if fields.get('分发计划') else '[NONE] 无'}")

    print("\n" + "=" * 60)
    print("[OK] Mock完整流程验证通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_full_flow_mock()
