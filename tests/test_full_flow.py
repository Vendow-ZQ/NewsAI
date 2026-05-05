"""快速验证完整流程 - 使用已有热帖数据绕过爬虫"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm

async def test_topic_curator():
    """测试小编Agent - 从已有热帖创建选题"""
    storage = FeishuStorage()
    llm = get_llm()
    
    # 检查热帖库
    from core.storage.interface import QueryFilter
    filters = [QueryFilter(field="状态", operator="eq", value="待选")]
    trends = storage.query("热帖库", filters=filters, limit=10)
    print(f"待选热帖数: {len(trends)}")
    
    if not trends:
        print("没有待选热帖，让小编无法工作")
        return
    
    # 手动运行小编Agent
    from core.agents.topic_curator import TopicCuratorAgent
    agent = TopicCuratorAgent(storage, llm)
    
    print("\n运行小编Agent...")
    result = agent.execute({"koc_id": "KOC-001"})
    print(f"小编生成选题数: {result.get('count', 0)}")
    
    # 检查选题库
    topics = storage.query("选题库", filters=[], limit=10)
    print(f"选题库现有: {len(topics)}条")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_topic_curator())
