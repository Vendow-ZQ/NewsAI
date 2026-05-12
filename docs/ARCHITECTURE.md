# NewsAI 系统架构文档

> 本文档描述 NewsAI v3.0 的系统架构、数据流和核心设计决策。
> 
> 版本：v3.0  
> 更新日期：2026-05-12

---

## 1. 系统概述

NewsAI 是一个运行在飞书多维表格上的 AI 虚拟新闻编辑部，由 9 个 AI Agent 组成，7×24 自动完成信息采集 → 选题策划 → 内容生产 → 审核修改 → 多平台分发 → 数据分析的全流程。

### 1.1 核心设计理念

| 设计理念 | 说明 |
|---------|------|
| **Bitable-Only** | 所有数据存储在飞书多维表格，零外部数据库依赖 |
| **状态机驱动** | 通过 Bitable 表状态流转驱动流程，非内存状态 |
| **Agent 化** | 每个角色一个 Agent，独立职责，标准化接口 |
| **工程级 Prompt** | XML 结构化 + Few-Shot + 自检清单 |
| **人机协作** | 关键节点人工可接管、可干预、可审核 |

---

## 2. 组织架构

### 2.1 4 部门 + 1 独立

```
总裁办（KOC 本人）
    │
    ├── 信息组（Intelligence Dept.）
    │   └── 小哨 TrendScout (EMP-001) · 信息官
    │       职责：7大信息源监控 → 21条热帖/轮 → 热度评分+标签
    │
    ├── 决策组（Editorial Dept.）
    │   └── 小编 TopicCurator (EMP-002) · 选题总编
    │       职责：3关筛查 → 5维度爆点拆解 → 3条候选选题
    │
    ├── 生产组（Production Dept.）· 3人并行
    │   ├── 小文 ContentWriter (EMP-003) · 文字编辑
    │   │   职责：长文源稿（1000-3000字，不分平台）
    │   ├── 小图 VisualDesigner (EMP-004) · 视觉设计师
    │   │   职责：5-8张图素材池（文字卡片/信息图/AI画面）
    │   └── 小播 ScriptWriter (EMP-005) · 短视频编剧
    │       职责：主视频脚本（1-3分钟，含分镜/口播/字幕）
    │
    ├── 治理组（Governance Dept.）· 审改循环
    │   ├── 小审 Reviewer (EMP-006) · 审核员
    │   │   职责：4维度审查（事实/风险/人设/合规）
    │   └── 小改 Editor (EMP-007) · 修改专员
    │       职责：精确修改 + changelog生成（diff格式）
    │
    ├── 分发组（Distribution Dept.）
    │   └── 小发 Distributor (EMP-008) · 分发策略师
    │       职责：5平台版本拆分 + 分发计划（时间×受众）
    │
    └── 独立复盘组（Analytics Unit）
        └── 小数 Analyst (EMP-009) · 数据分析师
            职责：数据回流 → 爆点验证 → 月度经验沉淀
```

### 2.2 汇报关系

- **小编 + 小数**：直接向 KOC 汇报
- **生产组 3 人**：向小编汇报（选题负责人）
- **审改组 2 人**：治理组内部循环，最终向小编汇报
- **小发**：向小编汇报（执行层）
- **小哨**：独立采集，支持决策组

---

## 3. 技术架构

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│  应用层 (Application Layer)                              │
│  ├── bootstrap.py         # 一键初始化                   │
│  ├── run.py               # 主入口（CLI）                │
│  └── 各种调试脚本                                         │
├─────────────────────────────────────────────────────────┤
│  编排层 (Orchestration Layer)                            │
│  ├── LangGraph StateGraph  # 状态图编排                  │
│  ├── NewsAIState          # 共享状态定义                 │
│  ├── nodes.py             # Agent节点包装器              │
│  └── edges.py             # 审改循环条件边               │
├─────────────────────────────────────────────────────────┤
│  业务层 (Business Layer)                                 │
│  ├── 9个Agent实现                                        │
│  │   ├── BaseAgent        # 抽象基类（模板方法模式）     │
│  │   └── 8个具体Agent                                    │
│  ├── Prompts共享模块                                     │
│  │   ├── koc_persona.py   # KOC人设渲染                  │
│  │   └── chinese_hooks.py # 中文爆款基因库               │
│  └── 信息源采集                                          │
│      └── 7个mock数据源                                   │
├─────────────────────────────────────────────────────────┤
│  适配层 (Adapter Layer)                                  │
│  ├── FeishuStorage        # Storage接口实现              │
│  ├── FeishuBaseManager    # Bitable操作封装              │
│  └── FeishuDocStorage     # 飞书文档操作（v3.0）         │
├─────────────────────────────────────────────────────────┤
│  基础设施层 (Infrastructure Layer)                       │
│  ├── 飞书 Bitable         # 7张多维表格                  │
│  ├── 飞书 云文档          # 内容产物存储（v3.0）         │
│  └── 火山方舟 Doubao 2.0  # LLM模型                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心流程图

```
                    ┌─────────────────────────────────────┐
                    │           信息采集阶段               │
                    │  小哨 TrendScout (EMP-001)           │
                    │  从7个mock文件采集21条热帖           │
                    │  LLM打分(0-1) + 主题标签            │
                    └──────────────┬──────────────────────┘
                                   │ 写入 TREND 表
                                   ▼
                    ┌─────────────────────────────────────┐
                    │           选题策划阶段               │
                    │  小编 TopicCurator (EMP-002)         │
                    │  3关筛查 + 5维度爆点拆解             │
                    │  产出3条候选，自动选最优             │
                    │  创建 ASSET 内容资产                 │
                    └──────────────┬──────────────────────┘
                                   │ 写入 TOPIC 表
                                   ▼
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  小文 Content   │    │  小图 Visual    │    │  小播 Script    │
│  Writer (EMP-003)│   │  Designer(EMP-004)│   │  Writer(EMP-005)│
│                 │    │                 │    │                 │
│ 写长文源稿      │    │ 产5-8张图素材池 │    │ 写主视频脚本    │
│ (1000-3000字)   │    │ (3类图混搭)     │    │ (1-3分钟)       │
│ 创建飞书文档    │    │ 创建飞书文档    │    │ 创建飞书文档    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                    ┌─────────────────────────────────────┐
                    │      production_sync 节点            │
                    │      (Fan-in 合并点)                 │
                    │      等待3人全部完成                 │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │           审改循环阶段               │
                    │                                     │
                    │  ┌─────────┐    ┌─────────┐        │
                    │  │ 小审    │───▶│ 小改    │        │
                    │  │Reviewer │    │ Editor  │        │
                    │  │(EMP-006)│◀───│(EMP-007)│        │
                    │  └─────────┘    └─────────┘        │
                    │       │                             │
                    │       │ 最多3轮                     │
                    │       │ 第3轮强制通过               │
                    │       ▼                             │
                    │  通过 → 进入分发                    │
                    │  需修改 → 循环                      │
                    └──────────────┬──────────────────────┘
                                   │ 更新 ASSET 审改状态
                                   ▼
                    ┌─────────────────────────────────────┐
                    │           分发策略阶段               │
                    │  小发 Distributor (EMP-008)          │
                    │                                     │
                    │  步骤1：拆5平台版本                  │
                    │    - 公众号(1500-3000字)            │
                    │    - 小红书(300-500字+9图)          │
                    │    - 抖音(30-60秒口播)              │
                    │    - 视频号(1-3分钟)                │
                    │    - B站(1-3分钟教程)               │
                    │                                     │
                    │  步骤2：制定分发计划                 │
                    │    - 黄金时段错峰发布               │
                    │    - 受众标签+预期效果              │
                    └──────────────┬──────────────────────┘
                                   │ 创建5个分发文档
                                   ▼
                    ┌─────────────────────────────────────┐
                    │           数据分析阶段               │
                    │  小数 Analyst (EMP-009)              │
                    │                                     │
                    │  读mock数据按优先级匹配档位         │
                    │  综合评分(0-1) + 爆点验证           │
                    │  平台表现分析 + 选题建议            │
                    └──────────────┬──────────────────────┘
                                   │ 写入 DATA 表
                                   ▼
                                 END
```

---

## 4. 数据模型

### 4.1 表关系图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    信源配置      │       │    热帖库       │       │    选题库       │
│   (SOURCES)     │──────▶│   (TREND)      │──────▶│   (TOPIC)      │
│                 │       │                 │       │                 │
│ 7个信息源配置   │       │ 小哨采集的     │       │ 小编筛选的     │
│ 8条种子数据     │       │ 21条热帖/轮    │       │ 选题方案       │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             │ 关联资产ID
                                                             ▼
                                    ┌─────────────────────────────────────┐
                                    │         内容资产库 (ASSET)           │
                                    │                                     │
                                    │  id: ASSET-YYYYMMDD-XXXX            │
                                    │  选题ID: TOPIC-xxxxx                │
                                    │  选题标题: xxx                      │
                                    │  文案状态: 未开始/生产中/已完成     │
                                    │  配图状态: 未开始/生产中/已完成     │
                                    │  视频状态: 未开始/生产中/已完成     │
                                    │  审改状态: 未开始/审改中/已通过     │
                                    │  审改轮次: 0-3                      │
                                    │  分发状态: 未开始/已生成            │
                                    │                                     │
                                    │  文案文档链接 → 飞书文档           │
                                    │  图片提示词文档链接 → 飞书文档     │
                                    │  视频脚本文档链接 → 飞书文档       │
                                    │  审改文档链接 → 飞书文档           │
                                    │  分发计划JSON: {...}               │
                                    └────────┬────────────────────────────┘
                                             │
                                             │ 数据回流ID
                                             ▼
                                    ┌─────────────────────────────────────┐
                                    │          数据库 (DATA)               │
                                    │                                     │
                                    │  各平台阅读量/点赞数/播放量         │
                                    │  综合评分 + 爆点验证结果            │
                                    │  成败分析 + 选题建议                │
                                    └─────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────┐
│    KOC人设      │       │  Agent协作日志   │
│   (KOC_PERSONA) │       │   (AGENT_LOG)   │
│                 │       │                 │
│ 学AI的刘同学    │       │ 9个Agent工作轨迹│
│ 人设JSON        │       │ 执行时间/状态   │
└─────────────────┘       └─────────────────┘
```

### 4.2 关键状态流转

#### 选题状态流转 (TOPIC.选题状态)

```
待选 → 已选中 → 生产中 → 审改中 → 分发中 → 已发布
  │      │         │         │         │        │
  │      │         │         │         │        └── 小数完成数据分析
  │      │         │         │         └── 小发完成分发计划
  │      │         │         └── 小审/小改循环中
  │      │         └── 小文/小图/小播生产中
  │      └── 小编自动选中优先级最高的
  └── 小编刚创建，待选择
```

#### 资产状态流转 (ASSET)

```
文案状态：未开始 → 生产中 → 已完成
配图状态：未开始 → 生产中 → 已完成
视频状态：未开始 → 生产中 → 已完成
审改状态：未开始 → 审改中 → 已通过/已强制通过/卡死
分发状态：未开始 → 已生成
```

---

## 5. 核心设计模式

### 5.1 BaseAgent 模板方法模式

所有 Agent 继承自 `BaseAgent`，遵循统一的 5 步执行流程：

```python
class BaseAgent(ABC):
    def execute(self, context: dict) -> dict:
        # 1. 读取上游数据
        upstream_data = self._read_upstream(context)
        
        # 2. 调用工具（如需要）
        tool_results = self._invoke_tools(context, upstream_data)
        
        # 3. 调用 LLM 处理
        llm_result = self._invoke_llm(context, upstream_data, tool_results)
        
        # 4. 写入存储
        self._write_storage(context, llm_result)
        
        # 5. 写工作日志
        self._log_work(context, llm_result)
        
        return llm_result
```

**优势**：
- 标准化 Agent 开发流程
- 自动记录协作日志
- 统一错误处理和重试

### 5.2 LangGraph 状态机编排

```python
# 核心设计
workflow = StateGraph(NewsAIState)

# Fan-out：小编并发到生产组3人
workflow.add_edge("小编", "小文")
workflow.add_edge("小编", "小图")
workflow.add_edge("小编", "小播")

# Fan-in：3人完成后到 sync
workflow.add_edge("小文", "production_sync")
workflow.add_edge("小图", "production_sync")
workflow.add_edge("小播", "production_sync")

# 审改循环
workflow.add_conditional_edges(
    "小审",
    should_continue_review,
    {"继续审改": "小改", "审改完成": "小发"}
)
workflow.add_edge("小改", "小审")
```

**优势**：
- 可视化流程定义
- 支持复杂分支逻辑
- 状态持久化（可恢复）

### 5.3 Bitable 状态驱动（而非内存状态）

**关键设计决策**：流程推进依赖 Bitable 表状态，而非 LangGraph 内存状态。

```python
# Agent 读取上游数据时，查询 Bitable 状态
topics = self.storage.query("选题库")
active_topics = [t for t in topics if t.data.get("选题状态") == "生产中"]

# Agent 完成工作后，更新 Bitable 状态
self.storage.update("内容资产库", asset_id, {
    "文案状态": "已完成",
    "文案文档链接": doc_url,
})
```

**优势**：
- 流程可中断、可恢复
- 人工可随时介入查看状态
- 系统崩溃后可从中断点继续

---

## 6. Prompt 工程体系

### 6.1 Prompt 分层架构

```
Level 1: Agent System Prompt
  └── 位置：core/agents/{agent}.py 中的 SYSTEM_PROMPT
  └── 作用：定义角色、工作流、输出格式
  └── 特点：XML结构化分区，含self_check

Level 2: 共享 Prompt 模块
  ├── koc_persona.py
  │   └── render_koc_block(mode="identity/curation/creation/review/distribution/analytics")
  │   └── 注入KOC人设到所有Agent
  └── chinese_hooks.py
      └── CHINESE_HOOKS_BLOCK
      └── 中文爆款基因库（标题公式、焦虑词表等）

Level 3: User Prompt（动态构建）
  └── _build_user_prompt() 方法
  └── 组合上游数据（KOC + Topic + Trends/Asset）
  └── 添加当前任务特定的 rules 和 examples
```

### 6.2 Prompt 设计原则

1. **XML结构化分区**：role/context/rules/examples/self_check
2. **Few-Shot示例**：3+示例（正例+反例+边界例）
3. **人设翻译**：抽象人设→可执行标准（✅会做/❌不做）
4. **Thinking块**：强制CoT思考（≤200字）
5. **输出契约**：严格JSON schema + 字数上限
6. **自检清单**：输出前LLM自我review（6-8条检查项）

---

## 7. 飞书集成设计

### 7.1 Bitable 表设计

**7张表，全部产物存储在Bitable**：

| 表 | 记录数 | 核心字段 |
|---|--------|---------|
| 信源配置 | 8条(种子) | 平台名称、API端点、采集参数 |
| 热帖库 | 21条/轮 | 标题、摘要、热度评分、主题标签、状态 |
| 选题库 | 3条/轮 | 选题标题、角度、爆点、优先级、状态 |
| 内容资产库 | 1条/选题 | 文案/配图/视频/审改/分发状态 + 文档链接 |
| 数据库 | 1条/选题 | 各平台数据 + 综合评分 + 爆点验证 |
| KOC人设 | 1条(种子) | 人设JSON、领域、禁区、语言风格 |
| Agent协作日志 | 10+/轮 | AgentID、任务类型、输入摘要、输出摘要、耗时 |

### 7.2 飞书文档集成（v3.0）

长文本内容存储在飞书文档，Bitable存储链接：

```python
# 创建飞书文档
doc_id = doc_storage.create_post_doc(topic_title, date_str)
doc_storage.append_section(doc_id, markdown)
doc_storage.set_permissions(doc_id, share_type="tenant_readable")
doc_url = doc_storage.get_share_url(doc_id)

# 更新Bitable
self.storage.update("内容资产库", asset_id, {
    "文案文档链接": doc_url,
})
```

**产物类型**：
- 文案文档：长文源稿（Markdown格式）
- 配图文档：图素材池（5-8张图描述+prompt）
- 脚本文档：视频脚本（分镜/口播/字幕/BGM）
- 审改文档：累积追加格式（每轮审查+修改记录）
- 分发文档：5平台版本（各平台专属文案）

---

## 8. 审改循环机制

### 8.1 设计原理

真实编辑部都有审改机制，防止低质量内容流出。

### 8.2 流程

```
第1轮审查
  小审查4维度 × 3件资产
    ├── 全部通过 → 进入分发
    └── 发现问题 → 进入小改

第2轮审查（如需）
  小改精确修改 → 更新审改文档
  小审再审
    ├── 通过 → 进入分发
    └── 仍有问题 → 第3轮

第3轮审查（强制通过）
  无论是否通过，都进入分发
  保留遗留问题清单
  标记为"已强制通过"
```

### 8.3 防卡死机制

- **连续dispute检测**：如果小改连续3次认为"无需修改"，标记为"卡死"，需人工介入
- **遗留问题保留**：强制通过时，不清空issues清单，确保问题可追溯

---

## 9. 扩展性设计

### 9.1 添加新 Agent

1. 继承 `BaseAgent`
2. 实现 4 个抽象方法：`_read_upstream`, `_invoke_tools`, `_invoke_llm`, `_write_storage`
3. 定义 `SYSTEM_PROMPT`（XML结构化）
4. 在 `builder.py` 中添加节点和边
5. 在 `state.py` 中添加状态字段（如需要）

### 9.2 添加新信息源

1. 在 `core/sources/` 创建新采集器
2. 继承 `BaseSource`
3. 实现 `fetch()` 方法
4. 在 `bootstrap.py` 的信源配置中添加新源

### 9.3 添加新平台支持

1. 修改 `小发 DistributorAgent` 的 `SYSTEM_PROMPT_STEP1`
2. 在5平台基础上增加第6平台
3. 更新 `builder.py` 中的产物生成逻辑

---

## 10. 监控与调试

### 10.1 Agent 协作日志

每次 Agent 执行自动记录：
- AgentID、任务类型、关联业务ID
- 输入摘要、输出摘要
- 执行状态、耗时秒数
- 错误信息（如有）

查看方式：飞书 Bitable → Agent协作日志表

### 10.2 测试覆盖

- **单元测试**：`tests/` 目录，每个核心函数有测试
- **E2E测试**：`e2e_test_v2.py`，完整流程验证
- **冒烟测试**：`test_graph_smoke.py`，图结构验证

### 10.3 调试模式

```bash
# 单Agent调试
python run.py --agent content --topic TOPIC-xxx

# 查看详细日志
tail -f logs/last_run.log
```

---

## 11. 关键决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-05-04 | Bitable-only架构 | 飞书文档API权限复杂、评审环境兼容性差 |
| 2026-05-04 | 删除小析，新增小改 | 职责合并+专人修改，审改循环需要 |
| 2026-05-06 | Prompt工程v2.0 | 基于Anthropic最佳实践重写 |
| 2026-05-07 | 小发分两次LLM调用 | 步骤1拆5平台+步骤2出策略，降低单次复杂度 |
| 2026-05-12 | 文件夹结构整理 | 归档旧脚本，分离日志/报告/数据 |

---

## 12. 附录

### 12.1 文档索引

- [AGENT_PROMPTS_MASTER.md](AGENT_PROMPTS_MASTER.md) - 完整Prompt工程文档
- [AGENT_ROSTER.md](AGENT_ROSTER.md) - 9位虚拟员工档案
- [CONTENT_DESIGN.md](CONTENT_DESIGN.md) - 内容产物设计
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - 7张表结构定义
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 项目概述与商业模式
- [KOC_PERSONA.md](KOC_PERSONA.md) - KOC人设

### 12.2 外部参考

- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [The Prompt Report](https://arxiv.org/abs/2406.06608)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [飞书 OpenAPI](https://open.feishu.cn/document/ukTMukTMukTM/uATN4EjLwUTNx4yM1EjMx)

---

*NewsAI v3.0 架构文档 · 最后更新：2026-05-12*
