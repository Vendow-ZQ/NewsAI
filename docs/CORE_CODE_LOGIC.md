# NewsAI Core 核心代码运行逻辑

> 本文档描述从 `run.py` 入口到 9 个 Agent 执行完毕的完整调用链。
> 版本：v3.0 · 更新日期：2026-05-13

---

## 一、整体架构图

```
run.py (入口)
  │
  ▼
core/graph/builder.py  build_newsai_graph()
  │  ── 定义 10 个节点 + 条件边，构建 LangGraph StateGraph
  │
  ├──► 小哨 ──► 小编 ──► [Fan-out] 小文 ══╗
  │                                    小图 ══╬═► production_sync ──► 小审
  │                                    小播 ══╝                      ↓ 条件边
  │                                                              小改 ⟲ 最多3轮
  │                                                                  ↓
  │                                                               小发 ──► 小数 ──► END
  │
  └── 各节点包装器: core/graph/nodes.py
      └── 各 Agent 实现: core/agents/*.py
          └── 基类: core/agents/base.py  (模板方法模式)
```

---

## 二、入口层

### 2.1 run.py —— 程序入口

**位置**: `run.py:1`

**作用**: 命令行入口，支持两种模式：

| 命令 | 调用函数 | 说明 |
|------|----------|------|
| `python run.py --once` | `run_once()` | 跑一轮完整 LangGraph 流程 |
| `python run.py --once --topic TOPIC_ID` | `run_once(topic_id)` | 从指定选题开始跑 |
| `python run.py --agent trend` | `run_agent("trend")` | 单独调试某个 Agent |

**run_once 调用链**:
```python
run_once()
  ├── 实例化 FeishuStorage()      # feishu_adapter/feishu_storage.py
  ├── 实例化 get_llm()            # core/llm/client.py → ChatOpenAI(火山方舟)
  ├── 构建图: build_newsai_graph(storage, llm)   # core/graph/builder.py
  ├── 创建初始状态: NewsAIState(current_topic_id=topic_id)  # core/graph/state.py
  └── 执行: await graph.ainvoke(state)   # LangGraph 引擎驱动
```

---

## 三、编排层 (core/graph/)

### 3.1 builder.py —— 图构建工厂

**位置**: `core/graph/builder.py:31`

**作用**: 定义 LangGraph 的完整拓扑结构。

**10 个节点**:

| 节点名 | 创建函数 | 对应 Agent |
|--------|----------|-----------|
| 小哨 | `create_trend_scout_node()` | TrendScoutAgent |
| 小编 | `create_topic_curator_node()` | TopicCuratorAgent |
| 小文 | `create_content_writer_node()` | ContentWriterAgent |
| 小图 | `create_visual_designer_node()` | VisualDesignerAgent |
| 小播 | `create_script_writer_node()` | ScriptWriterAgent |
| production_sync | `create_production_sync_node()` | 无 Agent（状态检查） |
| 小审 | `create_reviewer_node()` | ReviewerAgent |
| 小改 | `create_editor_node()` | EditorAgent |
| 小发 | `create_distributor_node()` | DistributorAgent |
| 小数 | `create_analyst_node()` | AnalystAgent |

**边（流程定义）**:

```python
# 顺序边
小哨 → 小编
小编 → [小文, 小图, 小播]      # Fan-out: 并发执行
[小文, 小图, 小播] → production_sync  # Fan-in: 全部完成后汇合
production_sync → 小审

# 条件边（审改循环）
小审 ──条件边──► 小改 或 小发
  └── 判定函数: should_continue_review()  # core/graph/edges.py
小改 → 小审   # 循环边

# 顺序边
小审 → 小发
小发 → 小数
小数 → END
```

### 3.2 state.py —— 共享状态定义

**位置**: `core/graph/state.py:18`

**作用**: 定义 LangGraph 节点间传递的状态对象。

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_topic_id` | str | 当前选题 ID |
| `current_asset_id` | str | 当前内容资产 ID（v3 新增） |
| `koc_id` | str | KOC 人设 ID（默认 KOC-001） |
| `revision_count` | int | 审改轮次（0-3） |
| `max_revisions` | int | 最大审改轮次（默认 3） |
| `review_verdict` | str | "通过" / "需修改" |
| `errors` | List[str] | 错误列表（并发安全，Annotated+operator.add） |
| `execution_log` | List[dict] | 执行日志（并发安全） |

**并发安全设计**: `errors` 和 `execution_log` 使用 `Annotated[List, operator.add]`，多个并行节点同时写入时，LangGraph 自动合并列表。

### 3.3 nodes.py —— 节点包装器

**位置**: `core/graph/nodes.py`

**作用**: 将每个 Agent 包装为 LangGraph 节点函数。

**统一节点模式**:

```python
def create_xxx_node(storage, llm):
    def node(state: NewsAIState) -> Dict[str, Any]:
        try:
            agent = XxxAgent(storage, llm)
            result = agent.execute(_agent_context(state))   # 传入 topic_id/asset_id/koc_id
            return {"execution_log": _make_log("xxx", "完成", result=result)}
        except Exception as e:
            return {"execution_log": _make_log("xxx", "失败", error=str(e)), "errors": [str(e)]}
    return node
```

**特殊节点 —— production_sync**:

位置: `nodes.py:107`

作用: 检查生产组 3 人是否全部完成（文案/配图/视频状态都为"已完成"）。

- 如果全部完成：更新 ASSET.生产完成时间，更新 TOPIC.选题状态 = "审改中"
- 如果未完成：返回等待状态

**状态更新节点**:

- 小编节点：返回时更新 `current_topic_id` 和 `current_asset_id`
- 小审节点：返回时更新 `review_verdict` 和 `revision_count`

### 3.4 edges.py —— 条件边逻辑

**位置**: `core/graph/edges.py:6`

**作用**: 审改循环的条件判断。

```python
def should_continue_review(state) -> str:
    if state.revision_count >= state.max_revisions:
        return "审改完成"   # 强制通过
    if state.review_verdict == "需修改" and state.revision_count < state.max_revisions:
        return "继续审改"   # 进入小改
    return "审改完成"       # 正常通过
```

---

## 四、业务层 (core/agents/)

### 4.1 base.py —— BaseAgent 抽象基类

**位置**: `core/agents/base.py:23`

**作用**: 模板方法模式，定义所有 Agent 的 5 步执行流程。

```python
class BaseAgent(ABC):
    def execute(self, context: dict) -> dict:
        # Step 1: 读取上游数据
        upstream_data = self._read_upstream(context)

        # Step 2: 调用工具（如需要）
        tool_results = self._invoke_tools(context, upstream_data)

        # Step 3: 调用 LLM 处理
        llm_result = self._invoke_llm(context, upstream_data, tool_results)

        # Step 4: 写入存储
        self._write_storage(context, llm_result)

        # Step 5: 写工作日志
        self._log_work(context, llm_result)

        return llm_result
```

**子类必须/可选实现的方法**:

| 方法 | 必须 | 说明 |
|------|------|------|
| `_read_upstream()` | 可选 | 读取 KOC 人设 + 上游表数据 |
| `_invoke_tools()` | 必须 | 调用外部工具（mock 数据、状态切换等） |
| `_invoke_llm()` | 必须 | 调用 LLM，构建 prompt，解析输出 |
| `_write_storage()` | 可选 | 写入 Bitable / 创建飞书文档 |
| `_log_work()` | 已默认实现 | 写入 Agent 协作日志表 |

**辅助函数**:

- `parse_koc_data()`: 解析 KOC 人设表的 JSON 字段
- `current_timestamp_ms()`: 当前毫秒时间戳
- `today_str()`: 今天日期字符串

### 4.2 各 Agent 详解

---

#### 小哨 TrendScoutAgent (EMP-001)

**文件**: `core/agents/trend_scout.py:22`

**职责**: 从 7 个 mock 文件各抽 3 条 = 21 条热帖，LLM 打分 + 打标签，写入热帖库。

**调用链**:
```
_read_upstream()      → 读 KOC 人设表 (KOC-001)
_invoke_tools()       → 读 7 个 mock_data/*.json，随机各抽 3 条
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt() → invoke_with_retry()
_write_storage()      → 写 21 条记录到 热帖库 表
_log_work()           → 写 Agent 协作日志
```

**Prompt 位置**:
- System Prompt: `trend_scout.py:39` (类属性 `SYSTEM_PROMPT`)
- User Prompt: `_build_user_prompt()` 方法 (`trend_scout.py:148`)
- KOC 注入: `core/prompts/shared/koc_persona.py` (`render_koc_block(koc, mode="identity")`)

**输入**: context (空 或 topic_id)
**输出**: `{"raw_posts": [...], "evaluations": [...], "log_summary": "...", "trend_ids": [...]}`
**触发下一个**: 返回后 LangGraph 自动走 `小哨 → 小编` 边

---

#### 小编 TopicCuratorAgent (EMP-002)

**文件**: `core/agents/topic_curator.py:20`

**职责**: 从 21 条热帖中筛选 3 条候选选题，自动选优先级最高的，创建 ASSET 内容资产。

**调用链**:
```
_read_upstream()      → 读 KOC 人设 + 热帖库全部记录
_invoke_tools()       → 无（直接传递）
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt() → 3 条候选
_write_storage()      → 写 3 条到 选题库 + 自动选最优 + 创建 ASSET 记录
```

**Prompt 位置**:
- System Prompt: `topic_curator.py:27`
- User Prompt: `_build_user_prompt()` (`topic_curator.py:116`)
- KOC 注入: `render_koc_block(koc, mode="curation")`

**输入**: context (空)
**输出**: `{"candidates": [...], "selected_topic_id": "TOPIC-xxx", "asset_id": "ASSET-xxx"}`
**触发下一个**: 返回 `current_topic_id` + `current_asset_id`，LangGraph 走 `小编 → [小文, 小图, 小播]` 边

---

#### 小文 ContentWriterAgent (EMP-003)

**文件**: `core/agents/content_writer.py:21`

**职责**: 读选题 + 关联热帖，写 1 篇 1000-3000 字长文源稿，创建飞书文案文档。

**调用链**:
```
_read_upstream()      → 读 KOC 人设 + 选题库(已选中) + 关联热帖
_invoke_tools()       → 切换 ASSET.文案状态 = "生产中"
_invoke_llm()         → SYSTEM_PROMPT + CHINESE_HOOKS_BLOCK + _build_user_prompt()
_write_storage()      → 创建飞书文案文档 → 更新 ASSET.文案状态 = "已完成" + 文案文档链接
```

**Prompt 位置**:
- System Prompt: `content_writer.py:28`
- User Prompt: `_build_user_prompt()` (`content_writer.py:176`)
- KOC 注入: `render_koc_block(koc, mode="creation")`
- 中文爆款基因: `core/prompts/shared/chinese_hooks.py` (`CHINESE_HOOKS_BLOCK`)

**输入**: context (含 topic_id, asset_id)
**输出**: `{"long_form_content": {...}, "topic_id": "...", "asset_id": "...", "doc_url": "..."}`
**触发下一个**: 返回后走 `小文 → production_sync` 边

---

#### 小图 VisualDesignerAgent (EMP-004)

**文件**: `core/agents/visual_designer.py:19`

**职责**: 读选题 + 小文长文全文，产出 5-8 张图素材池，创建飞书配图文档。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题 + ASSET + 小文长文全文(从飞书文档读取)
_invoke_tools()       → 切换 ASSET.配图状态 = "生产中"
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt()
_write_storage()      → 创建飞书配图文档 → 更新 ASSET.配图状态 = "已完成"
```

**Prompt 位置**:
- System Prompt: `visual_designer.py:26`
- User Prompt: `_build_user_prompt()` (`visual_designer.py:186`)
- KOC 注入: `render_koc_block(koc, mode="visual")`

**输入**: context (含 topic_id, asset_id)
**输出**: `{"image_pool": [...], "strategy": "...", "topic_id": "...", "asset_id": "...", "doc_url": "..."}`
**触发下一个**: `小图 → production_sync`

---

#### 小播 ScriptWriterAgent (EMP-005)

**文件**: `core/agents/script_writer.py:18`

**职责**: 读选题 + 小文长文全文，写 1 个 1-3 分钟主视频脚本，创建飞书脚本文档。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题 + ASSET + 小文长文全文(从飞书文档读取，不限字数)
_invoke_tools()       → 切换 ASSET.视频状态 = "生产中"
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt()
_write_storage()      → 创建飞书脚本文档 → 更新 ASSET.视频状态 = "已完成"
```

**Prompt 位置**:
- System Prompt: `script_writer.py:25`
- User Prompt: `_build_user_prompt()` (`script_writer.py:162`)
- KOC 注入: `render_koc_block(koc, mode="creation")`

**输入**: context (含 topic_id, asset_id)
**输出**: `{"script": {...}, "topic_id": "...", "asset_id": "...", "doc_url": "..."}`
**触发下一个**: `小播 → production_sync`

---

#### 小审 ReviewerAgent (EMP-006)

**文件**: `core/agents/reviewer.py:19`

**职责**: 审查 3 件资产（长文 + 图素材池 + 视频脚本），4 维度审查，判定 pass / needs_revision。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题(生产中/审改中) + ASSET + 3件资产文档内容
_invoke_tools()       → 无
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt()
                        → v3 修复: 第3轮强制通过，保留遗留 issues
_write_storage()      → 创建/追加审改文档 → 更新 ASSET.审改状态 + 审改轮次
                        → 如果通过: 更新 TOPIC.选题状态 = "分发中"
```

**Prompt 位置**:
- System Prompt: `reviewer.py:26`
- User Prompt: `_build_user_prompt()` (`reviewer.py:174`)
- KOC 注入: `render_koc_block(koc, mode="review")`

**输入**: context (含 topic_id, asset_id, revision_count)
**输出**: `{"review_result": {"verdict": "通过|需修改", "issues": [...], ...}, "topic_id": "...", "asset_id": "..."}`
**触发下一个**: 返回 `review_verdict` + `revision_count`，由 `should_continue_review()` 条件边决定 → 小改 或 小发

---

#### 小改 EditorAgent (EMP-007)

**文件**: `core/agents/editor.py:20`

**职责**: 读审改文档（小审的 issues 清单），逐条精确修改，输出 changelog。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题(审改中) + ASSET + 审改文档内容
_invoke_tools()       → 无
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt()
                        → v3 修复: changelog 不能为空，否则抛 LLMOutputError
_write_storage()      → 追加修改章节到审改文档
                        → 检查连续 dispute 次数，≥3 次标记"卡死"
```

**Prompt 位置**:
- System Prompt: `editor.py:27`
- User Prompt: `_build_user_prompt()` (`editor.py:146`)
- KOC 注入: `render_koc_block(koc, mode="review")`

**输入**: context (含 topic_id, asset_id, revision_count)
**输出**: `{"edit_result": {"changelog": [...], "dispute_review": bool}, "topic_id": "...", "asset_id": "..."}`
**触发下一个**: `小改 → 小审`（循环边，回到小审再审）

---

#### 小发 DistributorAgent (EMP-008)

**文件**: `core/agents/distributor.py:20`

**职责**: 拆分为 5 平台版本 + 制定分发计划，创建 5 个飞书分发文档。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题(分发中) + ASSET + 3件资产终稿
_invoke_tools()       → 切换 ASSET.分发状态 = "生产中"
_invoke_llm()         → 分两次 LLM 调用:
                        步骤1: SYSTEM_PROMPT_STEP1 + _build_step1_prompt() → 5 平台版本
                        步骤2: SYSTEM_PROMPT_STEP2 + _build_step2_prompt() → 分发计划
_write_storage()      → 创建 5 个飞书分发文档 → 更新 ASSET.分发状态 = "已生成"
                        → 更新 TOPIC.选题状态 = "已发布"
```

**Prompt 位置**:
- System Prompt Step1: `distributor.py:27`
- System Prompt Step2: `distributor.py:61`
- Step1 User Prompt: `_build_step1_prompt()` (`distributor.py:250`)
- Step2 User Prompt: `_build_step2_prompt()` (`distributor.py:364`)
- KOC 注入 Step1: `render_koc_block(koc, mode="creation")`
- KOC 注入 Step2: `render_koc_block(koc, mode="distribution")`
- 中文爆款基因: `CHINESE_HOOKS_BLOCK`

**输入**: context (含 topic_id, asset_id)
**输出**: `{"platform_versions": {...}, "distribution_plan": {...}, "topic_id": "...", "asset_id": "...", "doc_urls": {...}}`
**触发下一个**: `小发 → 小数`

---

#### 小数 AnalystAgent (EMP-009)

**文件**: `core/agents/analyst.py:19`

**职责**: 读取已发布选题，读 mock 数据按优先级匹配档位，LLM 分析综合评分 + 爆点验证。

**调用链**:
```
_read_upstream()      → 读 KOC + 选题(已发布)
_invoke_tools()       → 读 mock_data/analytics_mock.json，按选题优先级匹配档位
_invoke_llm()         → SYSTEM_PROMPT + _build_user_prompt()
_write_storage()      → 写 DATA 表记录 → 更新 TOPIC.数据回流ID
```

**Prompt 位置**:
- System Prompt: `analyst.py:26`
- User Prompt: `_build_user_prompt()` (`analyst.py:161`)
- KOC 注入: `render_koc_block(koc, mode="analytics")`

**输入**: context (含 topic_id)
**输出**: `{"analysis": {"综合评分": 0.85, "爆点验证": "验证成功", ...}, "topic_id": "...", "data_id": "DATA-xxx"}`
**触发下一个**: `小数 → END`（流程结束）

---

## 五、Prompt 体系

### 5.1 Prompt 三层架构

```
Level 1: Agent System Prompt（各 Agent 文件中的 SYSTEM_PROMPT 类属性）
  └── 定义角色、工作流、输出格式
  └── XML 结构化分区: <role>/<workflow>/<output_format>/<rules>/<self_check>

Level 2: 共享 Prompt 模块
  ├── core/prompts/shared/koc_persona.py
  │   └── render_koc_block(mode="identity|curation|creation|visual|review|distribution|analytics")
  │   └── 7 种模式，根据 Agent 职责注入不同的人设字段
  └── core/prompts/shared/chinese_hooks.py
      └── CHINESE_HOOKS_BLOCK
      └── 中文爆款基因库（标题公式、焦虑词表、6 大招式、平台分层、自检清单）

Level 3: User Prompt（各 Agent 的 _build_user_prompt() 方法）
  └── 动态构建，组合上游数据（KOC + Topic + Trends/Asset/Doc）
  └── 添加当前任务特定的 rules 和 examples
```

### 5.2 LLM 调用链

```python
# Agent._invoke_llm() 中
messages = [
    {"role": "system", "content": self.SYSTEM_PROMPT},
    {"role": "user", "content": user_content},   # koc_block + chinese_hooks + input + rules + self_check
]

thinking, answer, raw = invoke_with_retry(self.llm, messages, max_retries=3)
# 返回: thinking文本, answer字典, raw原始响应
```

**invoke_with_retry 调用链**:
```
core/utils/llm_output_parser.py:59
  ├── llm.invoke(messages)      # core/llm/client.py → ChatOpenAI(火山方舟)
  ├── parse_thinking_answer(raw)  # 解析 <thinking> + <answer> 标签
  │   └── 提取 JSON → dict
  └── 如果解析失败: 追加错误反馈给 LLM，最多重试 3 次
```

---

## 六、存储层

### 6.1 FeishuStorage —— Bitable 存储

**位置**: `feishu_adapter/feishu_storage.py:22`

**作用**: 封装所有 Bitable CRUD 操作。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `create(table, data)` | 创建记录，自动生成业务 ID |
| `update(table, record_id, data)` | 更新记录 |
| `query(table, filters, limit)` | 查询记录 |
| `get_by_id(table, record_id)` | 按业务 ID 获取单条记录 |
| `delete(table, record_id)` | 删除记录 |

**业务 ID 生成**: `core/storage/id_generator.py`
- 格式: `{PREFIX}-{YYYYMMDD}-{NNN}`
- 例: `TREND-20260513-001`, `TOPIC-20260513-001`

### 6.2 FeishuDocStorage —— 飞书云文档存储

**位置**: `feishu_adapter/docs/feishu_doc_storage.py:29`

**作用**: 创建/追加/读取飞书 Docx 文档。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `create_doc(title)` | 创建空白 Docx，返回 document_id |
| `append_section(doc_id, markdown)` | Markdown → 飞书 Block，追加到文档 |
| `read_doc_content(doc_id)` | 读取文档纯文本 |
| `get_share_url(doc_id)` | 构造分享链接 |
| `set_permissions(doc_id, share_type)` | 设置文档权限 |

**被谁调用**:
- 小文: `create_post_doc()` → 文案文档
- 小图: `create_doc()` → 配图文档
- 小播: `create_doc()` → 脚本文档
- 小审: `create_doc()` / `append_section()` → 审改文档（累积追加）
- 小发: `create_doc()` → 5 个平台分发文档

### 6.3 7 张 Bitable 表

| 表名 | 存储内容 | 谁读 | 谁写 |
|------|----------|------|------|
| 信源配置 | 7 个信息源配置 | 小哨 | bootstrap |
| 热帖库 | 21 条热帖/轮 | 小编、小审 | 小哨 |
| 选题库 | 选题方案 + 状态 | 小文/小图/小播/小审/小发/小数 | 小编、小审、小发 |
| 内容资产库 | 资产状态 + 文档链接 | 小图/小播/小审/小改/小发 | 小文/小图/小播/小审/小发 |
| 数据库 | 数据分析结果 | - | 小数 |
| KOC人设 | KOC 人设 JSON | 所有 Agent | bootstrap |
| Agent协作日志 | 执行轨迹 | - | 所有 Agent (自动) |

---

## 七、状态流转全图

### 7.1 TOPIC.选题状态

```
待选择 → 已选中 → 生产中 → 审改中 → 分发中 → 已发布
  │        │         │         │         │        │
  │        │         │         │         │        └── 小数完成
  │        │         │         │         └── 小发完成
  │        │         │         └── 小审通过 (或强制通过)
  │        │         └── 小文/小图/小播生产中
  │        └── 小编自动选中
  └── 小编刚创建
```

### 7.2 ASSET 状态

```
文案状态: 未开始 → 生产中 → 已完成
配图状态: 未开始 → 生产中 → 已完成
视频状态: 未开始 → 生产中 → 已完成
审改状态: 未开始 → 审改中 → 已通过 / 已强制通过 / 卡死
分发状态: 未开始 → 已生成
```

---

## 八、完整调用链示例（单轮流程）

```bash
$ python run.py --once
```

```
1. run.py:run_once()
   └── 初始化 FeishuStorage + get_llm
   └── build_newsai_graph(storage, llm)
       └── 创建 10 个节点 + 条件边
   └── graph.ainvoke(NewsAIState())

2. 【小哨节点】create_trend_scout_node()
   └── TrendScoutAgent.execute()
       ├── _read_upstream() → KOC-001
       ├── _invoke_tools() → mock_data/*.json × 7 = 21 条
       ├── _invoke_llm()
       │   ├── SYSTEM_PROMPT (trend_scout.py:39)
       │   ├── render_koc_block(mode="identity")
       │   └── invoke_with_retry() → core/llm/client.py → 火山方舟
       ├── _write_storage() → 热帖库.create() × 21
       └── _log_work() → Agent协作日志.create()

3. 【小编节点】create_topic_curator_node()
   └── TopicCuratorAgent.execute()
       ├── _read_upstream() → KOC + 热帖库全部
       ├── _invoke_llm()
       │   ├── SYSTEM_PROMPT (topic_curator.py:27)
       │   ├── render_koc_block(mode="curation")
       │   └── invoke_with_retry()
       ├── _write_storage()
       │   ├── 选题库.create() × 3
       │   ├── 自动选最优 → 选题状态 = "已选中"
       │   └── 内容资产库.create() (ASSET)
       └── 返回 {current_topic_id, current_asset_id}

4. 【Fan-out: 小文/小图/小播 并发执行】
   └── ContentWriterAgent.execute()     → 创建文案文档 → ASSET.文案状态=已完成
   └── VisualDesignerAgent.execute()    → 创建配图文档 → ASSET.配图状态=已完成
   └── ScriptWriterAgent.execute()      → 创建脚本文档 → ASSET.视频状态=已完成

5. 【production_sync 节点】
   └── 检查 ASSET 三状态是否都 = "已完成"
   └── 是 → 更新 TOPIC.选题状态 = "审改中"

6. 【小审节点】ReviewerAgent.execute()
   └── 读取 3 件资产文档内容
   └── _invoke_llm() → 4 维度审查
   └── _write_storage() → 创建审改文档 → 更新 ASSET.审改状态
   └── 如果通过 → 更新 TOPIC.选题状态 = "分发中"

7. 【条件边】should_continue_review()
   └── 需修改 → 走 "继续审改" → 小改
   └── 通过   → 走 "审改完成" → 小发

8. 【审改循环】(如需)
   └── 小改: 读审改文档 → LLM 修改 → 追加修改章节 → 回到小审
   └── 最多 3 轮

9. 【小发节点】DistributorAgent.execute()
   └── 步骤1: LLM 拆 5 平台版本
   └── 步骤2: LLM 出分发策略
   └── _write_storage() → 创建 5 个分发文档
   └── 更新 ASSET.分发状态 = "已生成"
   └── 更新 TOPIC.选题状态 = "已发布"

10. 【小数节点】AnalystAgent.execute()
    └── 读 analytics_mock.json
    └── _invoke_llm() → 综合评分 + 爆点验证
    └── _write_storage() → 数据库.create() + TOPIC.数据回流ID

11. 【END】流程结束
```

---

## 九、文件索引

| 文件 | 作用 | 关键类/函数 |
|------|------|------------|
| `run.py` | 程序入口 | `run_once()`, `run_agent()` |
| `core/graph/builder.py` | 图构建 | `build_newsai_graph()` |
| `core/graph/state.py` | 状态定义 | `NewsAIState` |
| `core/graph/nodes.py` | 节点包装器 | `create_*_node()` × 10 |
| `core/graph/edges.py` | 条件边 | `should_continue_review()` |
| `core/agents/base.py` | Agent 基类 | `BaseAgent.execute()` |
| `core/agents/trend_scout.py` | 小哨 | `TrendScoutAgent` |
| `core/agents/topic_curator.py` | 小编 | `TopicCuratorAgent` |
| `core/agents/content_writer.py` | 小文 | `ContentWriterAgent` |
| `core/agents/visual_designer.py` | 小图 | `VisualDesignerAgent` |
| `core/agents/script_writer.py` | 小播 | `ScriptWriterAgent` |
| `core/agents/reviewer.py` | 小审 | `ReviewerAgent` |
| `core/agents/editor.py` | 小改 | `EditorAgent` |
| `core/agents/distributor.py` | 小发 | `DistributorAgent` |
| `core/agents/analyst.py` | 小数 | `AnalystAgent` |
| `core/prompts/shared/koc_persona.py` | KOC 人设注入 | `render_koc_block()` |
| `core/prompts/shared/chinese_hooks.py` | 中文爆款基因 | `CHINESE_HOOKS_BLOCK` |
| `core/llm/client.py` | LLM 客户端 | `get_llm()` → ChatOpenAI |
| `core/utils/llm_output_parser.py` | 输出解析 | `invoke_with_retry()`, `parse_thinking_answer()` |
| `core/storage/id_generator.py` | ID 生成 | `IDGenerator.generate()` |
| `feishu_adapter/feishu_storage.py` | Bitable 存储 | `FeishuStorage` |
| `feishu_adapter/docs/feishu_doc_storage.py` | 文档存储 | `FeishuDocStorage` |
