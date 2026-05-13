"""Quick test of all 9 agents"""
import os
import sys

# Suppress verbose logging
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_agents():
    """Test all agents in sequence"""
    print("=" * 60)
    print("NewsAI v3.0 Agent 端到端测试")
    print("=" * 60)

    # 1. 小哨 TrendScout
    print("\n[1/9] 测试 小哨 TrendScout...")
    try:
        from core.agents.trend_scout import TrendScoutAgent
        agent = TrendScoutAgent()
        result = agent.execute({})
        trend_ids = result.get('trend_ids', [])
        print(f"  ✓ 小哨 完成: 写入 {len(trend_ids)} 条热帖")
    except Exception as e:
        print(f"  ✗ 小哨 失败: {e}")

    # 2. 小编 TopicCurator
    print("\n[2/9] 测试 小编 TopicCurator...")
    try:
        from core.agents.topic_curator import TopicCuratorAgent
        agent = TopicCuratorAgent()
        result = agent.execute({})
        topic_id = result.get('topic_id', 'unknown')
        print(f"  ✓ 小编 完成: 选题 {topic_id}")
    except Exception as e:
        print(f"  ✗ 小编 失败: {e}")

    # 3. 小文 ContentWriter
    print("\n[3/9] 测试 小文 ContentWriter...")
    try:
        from core.agents.content_writer import ContentWriterAgent
        agent = ContentWriterAgent()
        result = agent.execute({})
        doc_url = result.get('doc_url', '')
        print(f"  ✓ 小文 完成: 文档 {doc_url[:50]}..." if doc_url else "  ✓ 小文 完成")
    except Exception as e:
        print(f"  ✗ 小文 失败: {e}")

    # 4. 小图 VisualDesigner
    print("\n[4/9] 测试 小图 VisualDesigner...")
    try:
        from core.agents.visual_designer import VisualDesignerAgent
        agent = VisualDesignerAgent()
        result = agent.execute({})
        image_pool = result.get('image_pool', [])
        print(f"  ✓ 小图 完成: {len(image_pool)} 张图素材")
    except Exception as e:
        print(f"  ✗ 小图 失败: {e}")

    # 5. 小播 ScriptWriter
    print("\n[5/9] 测试 小播 ScriptWriter...")
    try:
        from core.agents.script_writer import ScriptWriterAgent
        agent = ScriptWriterAgent()
        result = agent.execute({})
        doc_url = result.get('doc_url', '')
        print(f"  ✓ 小播 完成: 脚本 {doc_url[:50]}..." if doc_url else "  ✓ 小播 完成")
    except Exception as e:
        print(f"  ✗ 小播 失败: {e}")

    # 6. 小审 Reviewer
    print("\n[6/9] 测试 小审 Reviewer...")
    try:
        from core.agents.reviewer import ReviewerAgent
        agent = ReviewerAgent()
        result = agent.execute({})
        verdict = result.get('review_result', {}).get('verdict', 'unknown')
        print(f"  ✓ 小审 完成: 判定 {verdict}")
    except Exception as e:
        print(f"  ✗ 小审 失败: {e}")

    # 7. 小改 Editor (循环修改)
    print("\n[7/9] 测试 小改 Editor...")
    try:
        from core.agents.editor import EditorAgent
        agent = EditorAgent()
        result = agent.execute({})
        print(f"  ✓ 小改 完成")
    except Exception as e:
        print(f"  ✗ 小改 失败: {e}")

    # 8. 小发 Distributor
    print("\n[8/9] 测试 小发 Distributor...")
    try:
        from core.agents.distributor import DistributorAgent
        agent = DistributorAgent()
        result = agent.execute({})
        doc_urls = result.get('doc_urls', {})
        print(f"  ✓ 小发 完成: {len(doc_urls)} 个平台文档")
    except Exception as e:
        print(f"  ✗ 小发 失败: {e}")

    # 9. 小数 Analyst
    print("\n[9/9] 测试 小数 Analyst...")
    try:
        from core.agents.analyst import AnalystAgent
        agent = AnalystAgent()
        result = agent.execute({})
        data_id = result.get('data_id', 'unknown')
        print(f"  ✓ 小数 完成: DATA {data_id}")
    except Exception as e:
        print(f"  ✗ 小数 失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_agents()
