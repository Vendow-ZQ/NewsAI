# NewsAI Mock 数据说明

本目录包含 NewsAI 项目所需的完整 mock 数据体系，用于演示、测试和开发。

---

## 文件清单与统计

| # | 文件名 | 记录数 | 说明 |
|---|--------|--------|------|
| 1 | `src_sources.json` | 8 | 信源配置（5真实平台 + 3中文社媒Mock） |
| 2 | `trend_hotposts.json` | 30 | 热帖采集库 |
| 3 | `topic_topics.json` | 6 | 选题及生产流程 |
| 4 | `analytics_mock.json` | 20 | 内容发布后的多平台数据分析 |
| 5 | `agent_roster.json` | 9 | 虚拟员工花名册 |
| 6 | `arxiv_papers.json` | 20 | arXiv 论文 |
| 7 | `hackernews_hot.json` | 20 | HackerNews 热帖 |
| 8 | `github_trending.json` | 20 | GitHub 趋势仓库 |
| 9 | `reddit_posts.json` | 20 | Reddit 帖子 |
| 10 | `xiaohongshu_hot.json` | 20 | 小红书热门笔记 |
| 11 | `douyin_hot.json` | 20 | 抖音热门视频 |
| 12 | `x_hot.json` | 20 | X/Twitter 热门帖子 |

**总计：12个文件，213条记录**

---

## 业务表 Mock 数据

### 1. `src_sources.json` — 信源配置表
- **记录数**: 8条（5真实信源 + 3中文社媒Mock）
- **字段**: id、信源名称、信源类型、信源URL、采集状态、更新频率、权重、标签体系、最近采集、采集规则
- **信源**: arXiv、HackerNews、GitHub Trending、Reddit r/LocalLLaMA、Reddit r/MachineLearning、小红书(Mock)、抖音(Mock)、X/Twitter(Mock)

### 2. `trend_hotposts.json` — 热帖库
- **记录数**: 30条
- **字段**: id、信源ID、信源名称、热帖标题、原始链接、内容摘要、关键词、热度指标、发布时间、采集时间、处理状态、关联选题
- **处理状态分布**: 已分析(3)、已推荐(6)、待分析(21)
- **覆盖信源**: arXiv(6)、HackerNews(4)、GitHub(4)、Reddit r/LocalLLaMA(3)、Reddit r/MachineLearning(3)、小红书(5)、抖音(4)、X/Twitter(1)

### 3. `topic_topics.json` — 选题库
- **记录数**: 6条
- **字段**: id、选题标题、选题状态、关联热帖、内容类型、目标平台、爆点拆解、优先级、时间线、文档链接、分发计划、执行Agent、审改轮次、最终评分
- **状态分布**: 已发布(1)、生产中(2)、审改中(1)、待发布(1)、已推荐(1)
- **优先级**: P0(3)、P1(2)、P2(1)

### 4. `analytics_mock.json` — 数据分析表
- **记录数**: 20条
- **字段**: id、选题ID、选题标题、选题来源、核心爆点、内容类型、适合平台、各平台阅读/播放/点赞/评论/收藏等数据、综合评分、爆点验证、验证结论、数据采集时间、数据状态
- **综合评分范围**: 0.68 ~ 0.98
- **爆点验证**: 验证成功(17)、部分验证(3)
- **数据状态**: 已分析(14)、已迭代分析(6)

### 5. `agent_roster.json` — Agent 花名册
- **记录数**: 9条
- **字段**: id、Agent名称、Agent编码、所属部门、职责描述、技能清单、工作流节点、输入、输出、处理时长_平均、LLM模型、状态、创建时间、累计处理
- **部门**: 信息组(1)、决策组(1)、生产组(3)、治理组(3)、独立复盘(1)
- **Agent**: 小哨(TrendScout)、小编(TopicCurator)、小文(ContentWriter)、小图(VisualDesigner)、小播(ScriptWriter)、小审(Reviewer)、小改(Editor)、小发(Distributor)、小数(Analyst)
- **LLM模型**: Doubao-pro-32k(5)、Doubao-pro-128k(2)、Doubao-lite-32k(2)

---

## 平台信源 Mock 数据

### 6. `arxiv_papers.json` — arXiv 论文
- **记录数**: 20条
- **字段**: 标题、原文链接、原文摘要、原文语言、发布时间、信源平台、作者、分类、pdf链接、热点方向、热度分、讨论热度、热点理由
- **内容**: 2026年5月最新论文，涵盖 Agent 工具调用、VLM 长程决策、LLM 推理、RAG 可靠性、Agent 安全、医疗 AI、模型微调等方向
- **热度分范围**: 82 ~ 96

### 7. `hackernews_hot.json` — HackerNews 热帖
- **记录数**: 20条
- **字段**: 标题、原文链接、原文摘要、原文语言、发布时间、信源平台、作者、分数、评论数、hn链接、热点方向、内容类型、热点理由
- **内容**: 围绕 Codex、Claude Code、MCP、AI 定价、Agent 安全、开源 AI 等 2026 年技术社区热点
- **分数范围**: 37 ~ 1341

### 8. `github_trending.json` — GitHub 趋势
- **记录数**: 20个仓库
- **字段**: 标题、原文链接、原文摘要、原文语言、发布时间、信源平台、编程语言、热点方向、stars、今日新增
- **内容**: 涵盖 Coding Agent(2)、Agent SDK(2)、Agent Framework(1)、Agent Orchestration(1)、MCP(2)、Browser Agent(1)、RAG/Document AI(3)、Agent Memory(1)、Agent Platform(1)、LLM Eval(1)、Local LLM(1)
- **Stars范围**: 11,000 ~ 168,000

### 9. `reddit_posts.json` — Reddit 帖子
- **记录数**: 20条
- **字段**: id、标题、内容摘要、原文链接、发布时间、信源平台、子版块、作者、upvotes、评论数、阅览量、互动量、主题标签、热点方向、热点理由
- **子版块**: r/singularity(3)、r/ClaudeAI(2)、r/OpenAI(3)、r/ChatGPT(3)、r/vibecoding(3)、r/MachineLearning(3)、r/LocalLLaMA(3)
- **Upvotes范围**: 740 ~ 4,190

### 10. `xiaohongshu_hot.json` — 小红书热门
- **记录数**: 20条
- **字段**: id、标题、内容摘要、原文链接、发布时间、阅览量、互动量、主题标签、笔记类型、用户情绪、热点理由
- **笔记类型**: 参赛复盘、教程、趋势观察、产品复盘、情绪观察、方法论、学习工作流、求职干货、产品种草、实测复盘、运营方法论、体验分享、产品体验、工具横评、消费建议、认知框架、发布会前瞻、避坑指南
- **阅览量范围**: 43万 ~ 182万

### 11. `douyin_hot.json` — 抖音热门
- **记录数**: 20条
- **字段**: id、标题、内容摘要、原文链接、发布时间、阅览量、互动量、主题标签、热点方向、内容类型、热点理由
- **内容类型**: 事件解读、工具教程、发布会前瞻、行业解读、实测对比、观点短评、科普解释、风险分析、产品种草、实用教程、工具评测、运营方法论、实测复盘、学习教程、方法论、消费建议、教程、产品观察、趋势解读、认知观点
- **播放量范围**: 96万 ~ 421万

### 12. `x_hot.json` — X/Twitter 热门
- **记录数**: 20条
- **字段**: id、标题、内容摘要、原文链接、发布时间、阅览量、互动量、主题标签、作者、内容类型、热点方向、热点理由
- **内容类型**: 官方发布、产品更新、趋势话题、社区讨论、KOL观点、行业新闻、技术科普、技术长帖、安全更新、用户吐槽、资料整理、功能爆料、产品更新解读、架构观点、工作流案例
- **阅览量范围**: 39万 ~ 320万

---

## 数据关联关系

```
src_sources (信源)
    ↓
trend_hotposts (热帖) —— 通过 信源ID 关联
    ↓
topic_topics (选题) —— 通过 关联热帖 字段关联
    ↓
analytics_mock (数据) —— 通过 选题ID 关联

agent_roster (Agent) —— 独立元数据表
```

---

## 使用说明

### 加载数据
```python
import json

with open('mock_data/src_sources.json', 'r', encoding='utf-8') as f:
    sources = json.load(f)

with open('mock_data/trend_hotposts.json', 'r', encoding='utf-8') as f:
    trends = json.load(f)
```

### 选题状态机
```
已推荐 → 生产中 → 审改中 → 待发布 → 已发布
```

### 审改轮次
- 0轮：尚未开始审改
- 1轮：初审通过
- 2轮：二审通过
- 3轮：终审通过（最多3轮）

---

## 更新记录

- **2026-05**: 全面更新数据，时间线从 2024-2025 更新至 2026年5月
  - 热帖从 9 条扩展至 30 条
  - 各平台信源数据从 3~5 条统一扩展至 20 条
  - 数据分析表从 6 条扩展至 20 条，新增多平台分发表格字段
  - Agent 花名册新增编码、累计处理等字段
  - 内容主题聚焦：Vibe Coding、Codex vs Claude Code、MCP、AI Agent 安全、AI 求职/知识管理等 2026 年热点
