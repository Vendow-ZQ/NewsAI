# NewsAI Mock 数据说明

本目录包含 NewsAI v2 项目所需的完整 mock 数据体系，用于演示、测试和开发。

## 📊 业务表 Mock 数据

### 1. `src_sources.json` - SRC 信源配置表
- **用途**: 配置7个信息源的采集规则和参数
- **记录数**: 8条（5真实+3Mock）
- **包含字段**: 信源ID、名称、类型、采集状态、更新频率、权重、采集规则等

### 2. `trend_hotposts.json` - TREND 热帖库
- **用途**: 存储从各信源采集到的热帖数据
- **记录数**: 9条
- **包含字段**: 热帖ID、信源ID、标题、链接、摘要、热度指标、处理状态等

### 3. `topic_topics.json` - TOPIC 选题库
- **用途**: 存储小编推荐的选题及完整生产流程状态
- **记录数**: 6条（覆盖各状态：已发布、生产中、审改中、待发布、已推荐）
- **包含字段**: 选题ID、状态、爆点拆解、平台分发计划、文档链接、执行Agent等

### 4. `analytics_mock.json` - DATA 数据库（已存在）
- **用途**: 存储内容发布后的数据分析结果
- **记录数**: 6条
- **包含字段**: 各平台阅读量、点赞数、评论数、综合评分、爆点验证等

### 5. `agent_roster.json` - Agent 花名册
- **用途**: 定义9个虚拟员工的能力、职责和工作流
- **记录数**: 9条
- **包含字段**: Agent名称、部门、职责、技能、工作流节点、I/O、LLM模型等

## 🌐 平台信源 Mock 数据

### 6. `arxiv_papers.json` - arXiv 论文
- **记录数**: 5条近期AI论文
- **内容**: 包含Mamba-2、RAG-Fusion、DPO等热点研究

### 7. `hackernews_hot.json` - HackerNews 热帖
- **记录数**: 5条技术社区热帖
- **内容**: 开源替代品、行业分析、成本趋势等

### 8. `github_trending.json` - GitHub 趋势
- **记录数**: 5个热门仓库
- **内容**: llm-course、open-webui、llama.cpp等

### 9. `reddit_posts.json` - Reddit 帖子
- **记录数**: 5条（r/LocalLLaMA、r/MachineLearning等）
- **内容**: 本地部署、研究论文、框架对比等

### 10. `xiaohongshu_hot.json` - 小红书热门（已存在）
- **记录数**: 3条
- **内容**: AI工具测评、编程助手体验

### 11. `douyin_hot.json` - 抖音热门（已存在）
- **记录数**: 3条
- **内容**: Sora、AI女友、AI设计工具

### 12. `x_hot.json` - X/Twitter 热门（已存在）
- **记录数**: 3条
- **内容**: Gemini 2.5、Llama 4、Anthropic融资

## 🔗 数据关联关系

```
src_sources (信源)
    ↓
trend_hotposts (热帖) - 通过 信源ID 关联
    ↓
topic_topics (选题) - 通过 关联热帖 字段关联
    ↓
analytics_mock (数据) - 通过 选题ID 关联

agent_roster (Agent) - 独立元数据表
```

## 📝 使用说明

### 在 bootstrap.py 中使用
```python
import json

# 加载信源配置
with open('mock_data/src_sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)

# 加载热帖数据
with open('mock_data/trend_hotposts.json', 'r', encoding='utf-8') as f:
    trends = json.load(f)

# 创建到飞书Base...
```

### 数据状态机
选题状态流转：
```
已推荐 → 生产中 → 审改中 → 待发布 → 已发布
```

### 审改循环
审改轮次记录：
- 0轮：尚未开始审改
- 1轮：初审通过
- 2轮：二审通过
- 3轮：终审通过（最多3轮）

## 🎯 设计亮点

1. **完整性**: 覆盖全部7张业务表 + 7个信源平台
2. **真实性**: 基于2024-2025真实AI热点事件
3. **多样性**: 包含不同状态、类型、平台的数据
4. **关联性**: 表与表之间通过ID建立关联
5. **中文语境**: 结合中文社交媒体特点（小红书、抖音）

## 🔄 更新建议

- 定期更新热帖数据以反映最新AI趋势
- 根据业务调整信源权重和采集规则
- 补充更多Agent执行记录和性能数据
