#!/usr/bin/env python3
"""逐步测试 - 确保每一步都正确"""

import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from feishu_adapter.feishu_storage import FeishuStorage
from core.storage.interface import QueryFilter

class FastMockLLM:
    def invoke(self, prompt):
        prompt_str = str(prompt)
        if "选题" in prompt_str and "爆点" in prompt_str:
            return '{"是否适合": true, "选题标题": "AI新突破测试", "选题角度": "测试角度", "预估爆点": "测试爆点", "预估受众": "测试受众", "推荐优先级": 8}'
        elif "公众号" in prompt_str:
            return '{"公众号": {"标题": "测试标题", "摘要": "测试摘要", "正文": "测试正文内容", "配图说明": "测试配图"}, "小红书": {"标题": "测试", "正文": "测试", "标签": "#测试"}, "抖音": {"文案": "测试", "钩子": "测试", "CTA": "测试"}, "B站": {"标题": "测试", "简介": "测试", "正文": "测试"}}'
        elif "配图" in prompt_str:
            return '{"配图思路": "测试", "图片清单": [{"类型": "封面", "描述": "测试"}], "即梦提示词": "测试", "文字卡片HTML": "<div>测试</div>"}'
        elif "视频脚本" in prompt_str:
            return '{"抖音版": {"时长": "60秒", "钩子开场": "测试", "核心内容": "测试", "CTA": "测试", "BGM建议": "测试"}, "B站版": {"时长": "2分15秒", "开场": "测试", "分段": [{"时间段": "15-60秒", "内容": "测试"}], "结尾": "测试", "BGM建议": "测试"}}'
        elif "审查" in prompt_str:
            return '{"审查结论": "通过", "严重度": "低", "发现的问题": [], "审查指标": {"事实核查": "通过", "风险词扫描": "通过"}}'
        elif "分发" in prompt_str:
            return '{"分发计划": [{"平台": "公众号", "发布时间": "2026-05-05 18:00"}], "注意事项": "测试"}'
        elif "数据" in prompt_str:
            return '{"基础数据": {"阅读量": 1000}, "传播表现": {"打开率": 0.1}, "成败分析": "测试经验总结", "改进建议": "测试建议"}'
        return '{"result": "success"}'

def main():
    storage = FeishuStorage()
    llm = FastMockLLM()

    print("=" * 60)
    print("Step-by-step Test")
    print("=" * 60)

    # Step 1: 小编 - 创建选题
    print("\n[1] 小编创建选题...")
    from core.agents.topic_curator import TopicCuratorAgent
    curator = TopicCuratorAgent(storage, llm)
    result = curator.execute({'koc_id': 'KOC-001'})
    print(f"  创建选题: {result.get('count', 0)}条")

    # 获取刚创建的选题
    topics = storage.query('选题库', filters=[], limit=10)
    topic = None
    for t in topics:
        if t.data.get('状态') == '已选':
            topic = t.data
            break

    if not topic:
        print("  错误：没有已选选题")
        return

    topic_id = topic.get('id')
    print(f"  选题ID: {topic_id}, 状态: {topic.get('状态')}")

    # Step 2: 小文 - 生成内容
    print("\n[2] 小文生成帖子内容...")
    from core.agents.content_writer import ContentWriterAgent
    writer = ContentWriterAgent(storage, llm)
    result = writer.execute({'topic_id': topic_id})
    print(f"  生成内容: {result.get('count', 0)}条")

    # 检查状态
    t = storage.get_by_id('选题库', topic_id)
    print(f"  当前状态: {t.data.get('状态')}")
    print(f"  帖子内容: {'Y' if t.data.get('帖子内容') else 'N'}")

    # Step 3: 小播 - 生成脚本
    print("\n[3] 小播生成视频脚本...")
    from core.agents.script_writer import ScriptWriterAgent
    script = ScriptWriterAgent(storage, llm)
    result = script.execute({'topic_id': topic_id})
    print(f"  生成脚本: {result.get('count', 0)}条")

    # 检查
    t = storage.get_by_id('选题库', topic_id)
    print(f"  当前状态: {t.data.get('状态')}")
    print(f"  视频脚本: {'Y' if t.data.get('视频脚本内容') else 'N'}")

    # Step 4: 小审 - 审查
    print("\n[4] 小审查审查...")
    from core.agents.reviewer import ReviewerAgent
    reviewer = ReviewerAgent(storage, llm)
    result = reviewer.execute({'topic_id': topic_id})
    print(f"  审查完成: {result.get('count', 0)}条")

    # 检查
    t = storage.get_by_id('选题库', topic_id)
    print(f"  当前状态: {t.data.get('状态')}")
    print(f"  审改记录: {'Y' if t.data.get('审改记录') else 'N'}")

    # Step 5: 小发
    print("\n[5] 小发生成分发计划...")
    from core.agents.distributor import DistributorAgent
    dist = DistributorAgent(storage, llm)
    result = dist.execute({'topic_id': topic_id})
    print(f"  分发计划: {result.get('count', 0)}条")

    # 检查
    t = storage.get_by_id('选题库', topic_id)
    print(f"  分发计划: {'Y' if t.data.get('分发计划') else 'N'}")

    # Step 6: 小数
    print("\n[6] 小数数据分析...")
    from core.agents.analyst import AnalystAgent
    analyst = AnalystAgent(storage, llm)
    result = analyst.execute({'topic_id': topic_id})
    print(f"  数据分析: {result.get('count', 0)}条")

    # 最终检查
    print("\n" + "=" * 60)
    print("最终结果")
    print("=" * 60)
    t = storage.get_by_id('选题库', topic_id)
    f = t.data
    print(f"选题标题: {f.get('选题标题')}")
    print(f"状态: {f.get('状态')}")
    print(f"帖子内容: {'Y' if f.get('帖子内容') else 'N'} ({len(str(f.get('帖子内容', '')))}字)")
    print(f"视频脚本: {'Y' if f.get('视频脚本内容') else 'N'} ({len(str(f.get('视频脚本内容', '')))}字)")
    print(f"审改记录: {'Y' if f.get('审改记录') else 'N'} ({len(str(f.get('审改记录', '')))}字)")
    print(f"分发计划: {'Y' if f.get('分发计划') else 'N'}")

    # 检查数据库
    data = storage.query('数据库', filters=[], limit=10)
    print(f"数据库: {len(data)}条")
    if data:
        print(f"经验总结: {'Y' if data[0].data.get('经验总结') else 'N'}")

if __name__ == '__main__':
    main()
