#!/usr/bin/env python3
"""快速诊断测试 - 逐步执行定位问题"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.storage.interface import QueryFilter


def test_step_by_step():
    """逐步测试，定位卡住的环节"""

    print("[0] 初始化存储和LLM...")
    storage = FeishuStorage()
    llm = get_llm()
    print("  [OK] 初始化完成")

    # 1. 检查热帖库
    print("\n[1] 检查热帖库...")
    filters = [QueryFilter(field="状态", operator="eq", value="待选")]
    trends = storage.query("热帖库", filters=filters, limit=10)
    print(f"  [OK] 待选热帖: {len(trends)}条")

    if not trends:
        print("[ERR] 没有待选热帖")
        return

    # 2. 运行小编（简化版，不用LLM）
    print("\n[2] 运行小编Agent...")
    from core.agents.topic_curator import TopicCuratorAgent

    # 手动创建选题，绕过LLM
    from core.storage.id_generator import IDGenerator
    from datetime import datetime
    import json

    topic_id = IDGenerator.generate("TOPIC")
    record_data = {
        "业务ID": topic_id,
        "选题标题": f"测试选题-{datetime.now().strftime('%H%M%S')}",
        "选题角度": "测试角度",
        "预估爆点": "测试爆点",
        "预估受众": "测试受众",
        "关联热帖IDs": json.dumps([trends[0].data.get("业务ID", "")], ensure_ascii=False),
        "KOC人设ID": "KOC-001",
        "推荐优先级": 8,
        "状态": "已选",  # 关键：已选状态
        "审改轮次": 0,
        "创建时间": datetime.now().isoformat(),
        "创建者Agent": "测试脚本",
    }
    storage.create("选题库", record_data)
    print(f"  [OK] 创建选题: {topic_id}")

    # 3. 验证小文能读到
    print("\n[3] 验证小文读取...")
    filters = [QueryFilter(field="状态", operator="eq", value="已选")]
    topics = storage.query("选题库", filters=filters, limit=10)
    print(f"  [OK] 小文能读到选题: {len(topics)}条")

    # 4. 运行小文（尝试，可能LLM慢）
    print("\n[4] 运行小文Agent（限时10秒）...")
    from core.agents.content_writer import ContentWriterAgent

    writer = ContentWriterAgent(storage, llm)
    print("  小文Agent初始化完成，开始执行...")

    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("小文执行超时")

    # Windows不支持signal.SIGALRM，用简单方式
    try:
        result = writer.execute({"topic_id": topic_id})
        print(f"  [OK] 小文完成: {result.get('count', 0)}条内容")
    except Exception as e:
        print(f"  [WARN] 小文执行: {e}")

    # 5. 检查选题库更新
    print("\n[5] 检查选题库更新...")
    topics = storage.query("选题库", filters=[QueryFilter(field="业务ID", operator="eq", value=topic_id)], limit=1)
    if topics:
        fields = topics[0].data
        print(f"  状态: {fields.get('状态', 'N/A')}")
        print(f"  帖子内容: {'[OK] 有' if fields.get('帖子内容') else '[NONE] 无'}")

    print("\n[OK] 诊断完成")


if __name__ == "__main__":
    test_step_by_step()
