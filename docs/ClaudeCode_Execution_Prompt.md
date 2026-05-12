# NewsAI v3 自主冲刺执行指南

> 这是给 Claude Code CLI 的执行 prompt。
> 
> 启动方式：`claude --dangerously-skip-permissions`
> 然后整段粘贴此文件内容作为首条消息。

---

## 一、任务身份与目标

你是 Claude Code，正在为 ZQ 自主推进 NewsAI v3 重构。
ZQ 不在场，**全程不需要拍板**——所有决议已沉淀在 v3 文档中。
你按本文档执行，每完成 1 个 Task 就 push 一次代码。

**最终目标**：从当前的 v2-but-broken 代码状态，跑通完整的 v3 架构，端到端产出：
- 9 张飞书 Base 表（7 v2 留存 + TOPIC 瘦身版 + ASSET 新增）
- 1 条选题完整经历 9 个 Agent
- 9 个飞书云文档（1 文案 + 1 配图 + 1 脚本 + 1 审改 + 5 分发）
- 评委一打开能看到"工业级 AI 编辑部"

---

## 二、文档真源（必读，按优先级）

### L1 真理来源（必须先读，再动手）

| 路径 | 内容 | 必读章节 |
|---|---|---|
| `docs/Prompts_v3.md` | v3 完整 prompt 真源 | 全部 §0-§16 |
| `docs/SOP_v2.md` | 开发 SOP（v2 沉淀，仍适用）| §3 Stage 时间盒 |
| `docs/Tables_schema_v2.md` | 表 schema 设计 | 注：v3 覆盖 §2 TOPIC 和新增 ASSET |
| `docs/Agent_roster_v2.md` | 9 个 Agent 种子数据 | 全部 |
| `docs/KOC_persona.md` | KOC-001 学AI的刘同学人设 | 全部 |

### L2 实施参考

| 路径 | 内容 |
|---|---|
| `docs/Documents_design_v2.md` | 4 类文档结构（v3 仍适用）|
| `docs/NewsAI_workspace_v2.md` | 仓库结构和技术栈 |
| `docs/NewsAI_project_v2.md` | 产品愿景（粗读）|
| `docs/worklog.md` | 历史进度（参考但不依赖）|

### L3 不读

- 任何 `*_v1_deprecated.md`
- v1 残留代码（如 `core/agents/_archived/`）

---

## 三、执行总流程

```
START
  ↓
Step 0：环境检查（5 分钟）
  ↓
Step 1：通读 v3 文档（30 分钟）
  ↓
Step 2：patch 过期文档（5 分钟）
  ↓
Step 3：建 ASSET 表 + 修 TOPIC 表（30 分钟）⭐ 关键路径
  ↓
Step 4：实现 KOC 注入函数（30 分钟）⭐ 修复 Bug 1
  ↓
Step 5：实现 parse_thinking_answer 解析层（20 分钟）
  ↓
Step 6：重写 9 个 Agent prompt 文件（2 小时）⭐ 核心工作
  ↓
Step 7：实现 production_sync 节点（15 分钟）
  ↓
Step 8：升级 LangGraph builder（30 分钟）
  ↓
Step 9：mock_data 真实化（30 分钟）
  ↓
Step 10：端到端冒烟测试（30 分钟）
  ↓
Step 11：飞书 Base 视图美化（20 分钟）
  ↓
Step 12：最终验收 + 写总结 + push（15 分钟）
  ↓
END
```

**总时长估算**：6.5-7.5 小时。

**关键路径**（不能并行）：Step 3 → Step 4 → Step 6 → Step 8 → Step 10。

**可并行**（在主路径推进时同步做）：
- Step 5（解析层）+ Step 6（prompt 重写）
- Step 9（mock 数据）+ Step 4-6（任何时候）
- Step 11（视图美化）只在 Step 10 通过后做

---

## 四、详细 Step 说明

### Step 0：环境检查

**输入命令**：

```bash
cd D:/Code/NewsAI
git status
git log --oneline -10
python --version  # 要 3.11
pip list | grep -E "lark-oapi|langgraph|langchain|openai"
```

**验收**：
- ✅ git 工作区干净（或所有未提交都是预期内的）
- ✅ Python 3.11
- ✅ 4 个核心包都装了

**异常**：
- 工作区有未提交的破坏性改动 → 在 worklog 标记 + 跑 `git stash` 暂存，不丢弃
- 包缺失 → `pip install <package>` 补

---

### Step 1：通读 v3 文档

**动作**：

```bash
# 按顺序读，每读完一份在 worklog 标记
view docs/Prompts_v3.md  # 重点
view docs/Tables_schema_v2.md
view docs/Agent_roster_v2.md
view docs/KOC_persona.md
view docs/worklog.md  # 看最近进度
```

**理解检查（在 worklog 写一段确认）**：

完成后在 worklog 写：

```markdown
## YYYY-MM-DD HH:MM · Step 1 文档通读完成

【我理解的 v3 架构关键点】
1. 双表设计：TOPIC（瘦身决策）+ ASSET（生产流水）
2. 6 状态字段：选题/文案/配图/视频/审改/分发
3. 9 Agent + production_sync 节点
4. 5 个分发文档（公众号/小红书/抖音/视频号/B站）
5. KOC 必须通过 render_koc_block(koc, mode) 注入，禁默认值兜底
6. 小改 changelog 空 → dispute_review 字段，3 次 dispute 卡死
7. 小审第 3 轮强制通过保留 issues（forced_pass=true）

【需要重点修复的 5 个 bug】
Bug 1, 2, 3, 4, 11（按 v3 §16 修复对照表）

【其余 6 个 bug】已通过架构升级解决
```

---

### Step 2：patch 过期文档

```bash
# 2.1 Context.md 顶部加 v3 升级声明
view docs/Context.md
# 在最顶部加：
"""
> ⚠️ 架构升级提醒（2026-05-04 v3）：
> v3 在 v2 基础上拆出 ASSET 表、新增 6 状态字段、修复 5 个遗留 bug。
> 真源以 docs/Prompts_v3.md 为准。
> v3 与 Context.md 冲突时，以 v3 为准。
"""

# 2.2 KOC_persona.md 第 1.4 节修订
# 删 "小析 HookAnalyst"
# 加 "小改 Editor"（参考 Agent_roster_v2.md）

# 2.3 把 SOP.md 重命名归档
mv docs/SOP.md docs/SOP_v1_deprecated.md
# SOP_v2.md 已经是新版主用
```

**git commit**：
```bash
git add docs/
git commit -m "[v3 Step 2] patch 过期文档：Context 加 v3 声明 + KOC 修订 + SOP 归档"
```

---

### Step 3：建 ASSET 表 + 修 TOPIC 表 ⭐ 关键路径

#### 3.1 写 ASSET schema

新建文件 `feishu_adapter/base/schemas/asset_table.py`，按 Prompts_v3.md §2.2 实现。

#### 3.2 修 TOPIC schema

修改 `feishu_adapter/base/schemas/topic_table.py`，按 §2.1 瘦身：

**重要：v3 vs v2 的字段差异**：
- 删：帖子文档链接、视频脚本文档链接、审改文档链接（移到 ASSET）
- 删：分发计划 JSON、各类生产时间戳（移到 ASSET）
- 改：原"状态"字段 → "选题状态"（7 选项）
- 加：关联资产 ID

#### 3.3 写迁移脚本

新建 `scripts/migrate_v3.py`：

```python
"""v3 数据迁移：
1. 在飞书 Base 删除旧 TOPIC 字段（帖子文档链接等）
2. 在飞书 Base 新建 TOPIC 的"选题状态"字段（替代"状态"）
3. 在飞书 Base 新建"关联资产 ID"字段
4. 在飞书 Base 创建 ASSET 表（全部字段）
5. 清空所有旧数据（v3 重新跑端到端）
"""

# 实现逻辑：
# - 用 FeishuBaseManager 操作字段 CRUD
# - 跑前提醒"将清空数据，是否继续？"
```

#### 3.4 跑迁移

```bash
python scripts/migrate_v3.py --confirm
```

**验收**：
- ✅ 飞书 Base 看到 ASSET 表
- ✅ TOPIC 表瘦身（13 字段左右）
- ✅ 旧数据已清空

#### 3.5 git commit

```bash
git add feishu_adapter/base/schemas/asset_table.py
git add feishu_adapter/base/schemas/topic_table.py
git add scripts/migrate_v3.py
git commit -m "[v3 Step 3] 双表设计：新建 ASSET + 瘦身 TOPIC + 迁移脚本"
git push origin main
```

---

### Step 4：实现 KOC 注入函数 ⭐ 修复 Bug 1

按 Prompts_v3.md §1.1 完整实现 `core/prompts/shared/koc_persona.py`：

```python
KOC_RENDER_MODES = {"identity", "curation", "creation", "visual", "review", "distribution", "analytics"}

def render_koc_block(koc: dict, mode: str) -> str:
    """v3 强制要求：koc 不能为 None，否则抛 ValueError"""
    if not koc or not isinstance(koc, dict):
        raise ValueError("KOC 人设未提供，禁止默认值兜底")
    if mode not in KOC_RENDER_MODES:
        raise ValueError(f"非法 mode: {mode}")
    
    return MODE_RENDERERS[mode](koc)

# 7 个 mode 渲染函数...
```

**关键测试**：

```bash
# 创建 tests/prompts/test_koc_injection.py
python -m pytest tests/prompts/test_koc_injection.py -v
```

测试用例：
- `test_koc_required`：传 None 应抛 ValueError
- `test_invalid_mode`：传非法 mode 应抛
- `test_curation_mode`：渲染结果含 "禁区话题" 和 "✅ 会做" 标记
- `test_review_mode`：渲染结果含 "审查必检清单"

**验收**：测试全部 pass。

**git commit**：
```bash
git add core/prompts/shared/koc_persona.py
git add tests/prompts/test_koc_injection.py
git commit -m "[v3 Step 4] 修复 Bug 1：实现 render_koc_block + 单元测试"
git push origin main
```

---

### Step 5：实现 parse_thinking_answer 解析层

按 §1.3 实现 `core/utils/llm_output_parser.py`：

```python
def parse_thinking_answer(raw: str) -> Tuple[str, dict]:
    """提取 <thinking> 和 <answer>"""
    # ...

def invoke_with_retry(llm, messages, max_retries=3):
    """带重试的 LLM 调用，把错误反馈给 LLM 让它修正"""
    # ...
```

**关键测试**：`tests/utils/test_llm_parser.py`
- 正常格式解析成功
- 缺少 `<answer>` 抛 LLMOutputError
- JSON 解析失败抛 LLMOutputError
- markdown 代码块包裹的 JSON 也能解析

**git commit**：
```bash
git commit -m "[v3 Step 5] 实现 LLM 输出解析层 + invoke_with_retry"
git push origin main
```

---

### Step 6：重写 9 个 Agent prompt 文件 ⭐ 核心工作

按 §5-14 重写 10 个 prompt 文件（含小发分两步）：

| 文件 | v3 章节 | 关键改动 |
|---|---|---|
| `core/prompts/trend_scout.py` | §5 | 21 条统一 LLM + 工作摘要 |
| `core/prompts/topic_curator.py` | §6 | 一次产 3 条候选 |
| `core/prompts/content_writer.py` | §7 | 1 篇长文不分平台 |
| `core/prompts/visual_designer.py` | §8 | 5-8 张图素材池 |
| `core/prompts/script_writer.py` | §9 | 1 主脚本 + 读全文 |
| `core/prompts/reviewer.py` | §11 | 审三件 + 保留 issues |
| `core/prompts/editor.py` | §12 | 改副本 + dispute_review |
| `core/prompts/distributor_step1.py` | §13.2 | 拆 5 平台文案 |
| `core/prompts/distributor_step2.py` | §13.3 | 出分发策略 |
| `core/prompts/analyst.py` | §14 | 读 mock 文件不 random |
| `core/prompts/shared/chinese_hooks.py` | §1.2 | 中文爆款基因常量 |

**每个文件必须包含**：

```python
SYSTEM_PROMPT = """..."""
USER_TEMPLATE = """..."""
FEW_SHOT_EXAMPLES = [
    {"input": {...}, "thinking": "...", "output": {...}, "rationale": "..."},
    # 至少 3 个
]


def build_messages(koc: dict, **kwargs) -> list[dict]:
    """v3 强制要求：koc 必填"""
    if not koc:
        raise ValueError("koc 必填")
    
    user_content = USER_TEMPLATE.format(
        koc_persona_block=render_koc_block(koc, mode='xxx'),
        chinese_hooks_block=CHINESE_HOOKS_BLOCK,  # 如果需要
        **kwargs
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(...)},
        {"role": "user", "content": user_content},
    ]
```

**推进顺序**（按依赖关系）：

1. shared/chinese_hooks.py （独立）
2. trend_scout.py （独立）
3. topic_curator.py （独立）
4. content_writer.py / visual_designer.py / script_writer.py （独立，可并行）
5. reviewer.py （独立）
6. editor.py （独立）
7. distributor_step1.py / distributor_step2.py （独立）
8. analyst.py （独立）

**测试每个 prompt**：

每个 Agent 都加 `tests/prompts/test_<agent>_prompt.py`，至少 3 个测试：
- few_shot_consistency：few-shot 例子本身符合规则
- pass_case：正常输入应产出有效结果
- edge_case：边界输入（如小编全部热帖都触禁区）

**git commit 节奏**：每 2-3 个 prompt 文件 commit 一次。

```bash
git commit -m "[v3 Step 6.1] 重写小哨/小编/小文 prompt（含 few-shot 和测试）"
git commit -m "[v3 Step 6.2] 重写小图/小播 prompt（含 few-shot 和测试）"
git commit -m "[v3 Step 6.3] 重写小审/小改 prompt（含 few-shot 和测试）"
git commit -m "[v3 Step 6.4] 重写小发 step1/step2 + 小数 prompt（含 few-shot 和测试）"
git push origin main
```

---

### Step 7：实现 production_sync 节点

按 §10 实现 `core/graph/nodes/production_sync.py`。

**关键测试**：`tests/graph/test_production_sync.py`
- 3 状态全完成 → 切换 TOPIC.选题状态 = 审改中
- 任一状态未完成 → 抛错（不应该发生）

**git commit**：
```bash
git commit -m "[v3 Step 7] 实现 production_sync 节点 + 测试"
```

---

### Step 8：升级 LangGraph builder

修改 `core/graph/builder.py`，按 §10.3 的拓扑：

```python
# 关键改动：
# - 加 production_sync 节点
# - Fan-in 改为 [小文, 小图, 小播] → production_sync → 小审
# - 审改循环条件边检查 revision_count < 3
```

同时升级 `core/graph/state.py`，加 v3 字段：
- `revision_count: int = 0`
- `consecutive_dispute: int = 0`（v3 修复 Bug 4 用）
- `review_verdict: str = None`
- `forced_pass: bool = False`

**关键测试**：`tests/graph/test_v3_graph_topology.py`
- 9 个节点全部注册
- production_sync 节点存在
- 条件边路由正确

**git commit**：
```bash
git commit -m "[v3 Step 8] LangGraph builder 升级：加 production_sync + 审改循环"
git push origin main
```

---

### Step 9：mock_data 真实化

**9.1 用 web_search 联网搜索最近 AI 圈热点**

搜索关键词（至少 5 个）：
- "2026 年 5 月 AI 新闻"
- "Claude 4.7 发布"
- "GPT-5 最新"
- "AI Agent 最新"
- "AI 工具 2026"
- "Anthropic OpenAI 最新动态"

提取真实标题 + 内容摘要 + 阅读量量级。

**9.2 重写 7 个 mock 文件**

每个文件至少 8 条（小哨随机抽 3 条，需要冗余）：

```
mock_data/
├── xiaohongshu_hot.json    # 8+ 条小红书爆款
├── douyin_hot.json          # 8+ 条
├── x_hot.json               # 8+ 条
├── hackernews_hot.json      # 8+ 条
├── github_trending.json     # 8+ 条
├── arxiv_papers.json        # 8+ 条
└── reddit_posts.json        # 8+ 条
```

**字段统一**（每条）：

```json
{
  "id": "xhs_001",
  "标题": "...",
  "摘要": "...",
  "原文链接": "https://...",
  "原文语言": "中文",
  "发布时间": "2026-05-03",
  "阅览量": 125000,
  "互动量": 8200,
  "主题标签": ["新模型发布", "AI 工具"]
}
```

**9.3 写 analytics_mock.json**

按 §14.4 结构，3 档共 6 条数据。

**验收**：
- ✅ 7 个 mock 文件每个 ≥ 8 条
- ✅ 内容是真实改编的 AI 圈热点
- ✅ analytics_mock.json 3 档共 6 条

**git commit**：
```bash
git commit -m "[v3 Step 9] mock 数据真实化：7 文件各 8+ 条 + analytics 3 档 6 条"
git push origin main
```

---

### Step 10：端到端冒烟测试 ⭐ 验收里程碑

**10.1 跑 bootstrap.py v3**

如果 bootstrap.py 还没改造，先改：
- 创建 ASSET 表（如不存在）
- 创建 NewsAI产物/ 文件夹及 5 个子文件夹（文案/图片提示词/视频脚本/审改/分发）
- 种子数据：KOC + 9 Agent + 7 信源

```bash
python bootstrap.py
```

**10.2 跑端到端**

```bash
python run.py --once
```

**预期产出**：
- TREND 表：21 条新记录（每个 mock 源 3 条）
- TOPIC 表：3 条候选 + 1 条状态推进到"已发布"
- ASSET 表：1 条，所有状态字段已切换
- DATA 表：1 条数据回流
- LOG 表：≥ 12 条（每 Agent + production_sync + 审改循环额外几条）
- 飞书云空间 NewsAI产物/：
  - 文案/[文案] xxx.docx
  - 图片提示词/[配图] xxx.docx
  - 视频脚本/[脚本] xxx.docx
  - 审改/[审改] xxx.docx
  - 分发/[公众号] xxx.docx
  - 分发/[小红书] xxx.docx
  - 分发/[抖音] xxx.docx
  - 分发/[视频号] xxx.docx
  - 分发/[B站] xxx.docx

**10.3 失败排查**

如果某个 Agent 报错：
1. 看 LOG 表最后一条记录（Agent 花名 + 异常信息）
2. 看本地日志 `logs/newsai.log`
3. 定位到对应 Agent 文件
4. **不要 yolo 重跑**，先弄清失败原因

常见失败模式：
- `LLMOutputError: 缺少 <answer> 标签` → prompt 没让 LLM 用 XML 输出，检查 SYSTEM_PROMPT
- `ValueError: koc 必填` → build_messages 没传 koc，检查上游 _read_upstream
- `KeyError: '关联资产 ID'` → 选题库字段没正确创建，检查 schema
- 飞书 API `91403` 权限错误 → 应用没被加为 Base 协作者

**验收 checklist**（如果全 ✅，进 Step 11）：

```
□ 端到端无 fatal error
□ 9 张表数据完整
□ 9 个飞书云文档可点开
□ 至少 1 条选题状态推进到"已发布"
□ ASSET 表 6 个状态字段都有切换记录
□ 审改文档累积至少 1 轮审查 + 0-N 轮修改
□ 5 个分发文档内容差异化（不是复制粘贴）
```

**git commit**：
```bash
git commit -m "[v3 Step 10] 端到端冒烟通过 + bootstrap v3 升级"
git push origin main
```

---

### Step 11：飞书 Base 视图美化

**11.1 TOPIC 表视图**

按"选题状态"分列的看板视图：
- 待选择 / 已选中 / 生产中 / 审改中 / 分发中 / 已发布 / 已弃

**11.2 ASSET 表视图（4 个分组视图）**

- 视图 A · 生产状态：5 状态字段 + 关联
- 视图 B · 内容资产：4 内容文档链接
- 视图 C · 分发文档：5 分发文档链接 + 分发计划
- 视图 D · 审改追踪：审改状态 + 轮次 + 遗留问题

**11.3 Agent 花名册分组视图**

按"所属部门"分组（信息组/决策组/生产组/治理组/独立复盘）。

**11.4 Agent 协作日志分组视图**

按"Agent 花名"分组。

**git commit**：
```bash
git commit -m "[v3 Step 11] 飞书 Base 视图美化（看板 + 分组）"
git push origin main
```

---

### Step 12：最终验收 + 写总结 + push

**12.1 完整 checklist**

```
□ 飞书 Base 9 张表数据完整
□ 飞书云空间 NewsAI产物/ 5 子文件夹 + 9 文档/条选题
□ TOPIC 表至少 1 条选题"已发布"
□ ASSET 表对应 1 条所有状态推进完成
□ DATA 表 1 条数据回流
□ LOG 表 ≥ 12 条
□ 5 个分发文档内容差异化
□ 审改文档累积式追加可见
□ 各 Agent prompt 都用 KOC 注入函数
□ 端到端可重复跑通（清空数据 + bootstrap + run）
```

**12.2 写最终总结到 worklog**

```markdown
## 2026-05-04 23:00 v3 自主冲刺总结

### 完成 Steps
✅ Step 0-12 全部完成

### v3 核心改造
1. 双表设计：TOPIC 瘦身 + ASSET 新增（共 38 字段拆分到 13+25）
2. 6 状态字段细化：选题/文案/配图/视频/审改/分发
3. 5 个分发文档：公众号/小红书/抖音/视频号/B站
4. KOC 注入函数化（render_koc_block）
5. production_sync 节点解决 race condition
6. 审改循环修复（保留 issues + dispute_review 防卡死）

### 修复 11 个 bug
✅ Bug 1: KOC 人设注入（核心修复）
✅ Bug 2: 生产组 race condition（拆 ASSET + sync 节点）
✅ Bug 3: 小改不退状态（架构改造）
✅ Bug 4: changelog 空（dispute_review 字段）
✅ Bug 5: 小编一次 3 条
✅ Bug 6: 小图 5-8 张素材池
✅ Bug 7: 小播读全文（解除截断）
✅ Bug 8: 小数读 mock 文件（不 random）
✅ Bug 9: 21 条全 LLM
✅ Bug 11: 强制通过保留 issues

### 端到端实测
- 1 条选题完整经历 9 个 Agent + production_sync
- 共生成 9 个飞书云文档
- 总耗时：约 10 分钟
- Token 消耗：约 80k

### 飞书产物链接
- Base: https://xxx.feishu.cn/base/xxx
- 文档目录: https://xxx.feishu.cn/drive/folder/xxx

### 明日（5/5）建议下一步
- Stage 7: bootstrap 视图美化加固
- Stage 8: TrendAI 冲刺（PCG 截止 5/6 23:59）
- Stage 9: NewsAI 终交付准备
```

**12.3 最终 push**

```bash
git add docs/worklog.md
git commit -m "[v3 Final] 自主冲刺完成：9 Agent 端到端通过 + 11 Bug 修复"
git push origin main
```

---

## 五、出错处置

### 5.1 出错时**绝对不做**的事

- ❌ 不要 yolo 重跑大流程
- ❌ 不要 `git reset --hard` 丢弃未提交改动
- ❌ 不要跳过 Step 直接做下一个
- ❌ 不要修改 v3 文档以"绕过"问题
- ❌ 不要回退到 v2 设计

### 5.2 出错时**正确**的处置流程

```
出错
  ↓
[Step 1] 暂停当前 Task，不要继续
  ↓
[Step 2] 在 worklog 标记 "🛑 阻塞"，并描述：
  - 哪个 Step 哪个 Task
  - 完整错误堆栈
  - 已尝试的 1-2 个简单解决方案
  ↓
[Step 3] 决策：是否可以绕过推进？
  ├── 可以绕过（如某个测试失败但不影响主路径）
  │     → 在 worklog 标记 "⚠️ 已绕过，明日补"
  │     → 继续下一 Step
  │
  └── 不可绕过（如端到端崩溃）
        → 在 worklog 标记 "🚨 严重阻塞"
        → 写详细诊断报告
        → 停下，等 ZQ 处理（早上回来看）
```

### 5.3 常见错误模式与处置

| 错误模式 | 处置 |
|---|---|
| Doubao API 限流 / 超时 | 等 60 秒重试 1 次；仍失败 → 切换到 mock LLM 跑下游测试，标记"LLM 服务异常" |
| 飞书 91403 权限 | 应用未加为 Base 协作者 → 不能自己解决 → 标记阻塞等 ZQ |
| Token 超限 | 缩短 few-shot 例子（保留 2 个）或拆分 LLM 调用 |
| LLM 输出格式偏差 | invoke_with_retry 已处理；如 3 次后仍失败 → 标记该 Agent 阻塞，跳过继续 |
| 飞书云文档创建失败 | 检查文件夹 folder_token 是否正确；fallback：暂时写入 Bitable 多行文本字段，标记降级 |
| 测试失败但代码看起来对 | 先看测试本身是否符合 v3 规则；不是 LLM 黑盒别花太多时间 |
| Git push 冲突 | `git pull --rebase`；不要 `git push -f` |

### 5.4 阻塞时的 worklog 模板

```markdown
## YYYY-MM-DD HH:MM · 🚨 阻塞报告

### 阻塞点
Step X · Task Y

### 错误信息
```
（完整错误堆栈）
```

### 已尝试
1. ...
2. ...

### 我的诊断
（你认为根因是什么）

### 影响范围
- 此阻塞影响哪些后续 Step？
- 是否可以绕过先做其他 Step？

### 状态
- [ ] 可绕过推进
- [x] 等 ZQ 介入

### 当前进度快照
- 已完成 Step: ...
- 飞书 Base 状态: ...
- Git commit: ...
```

---

## 六、worklog 写作规范

### 6.1 每个 Step 完成必写

```markdown
## YYYY-MM-DD HH:MM · Step X 完成

### 完成内容
- 文件：core/prompts/topic_curator.py（新）
- 文件：tests/prompts/test_topic_curator.py（新）
- 测试：3 个测试用例全 pass

### 关键决策（如有）
- 因 Doubao token 限制，few-shot 例子从 4 个缩到 3 个

### 验收
- ✅ 单元测试通过
- ✅ 手工跑通：21 条热帖 → 3 条候选

### 下一 Step
Step X+1
```

### 6.2 每 commit 必写

```markdown
## YYYY-MM-DD HH:MM · commit
- commit hash: abc1234
- message: [v3 Step 4] 修复 Bug 1：实现 render_koc_block
- 改动文件：3 个
```

### 6.3 节奏

- **每个 Step 完成立即写 worklog 一段**
- **每个 commit 后追加 commit 信息**
- **每个阻塞立即写阻塞报告**
- worklog 是 ZQ 早上回来看的"日记"——写清楚、不省略

---

## 七、Git 策略

### 7.1 分支模型

只用 `main` 分支。每个 Step 完成 commit + push。

### 7.2 Commit 消息规范

```
[v3 Step X] 简要说明

例：
[v3 Step 3] 双表设计：新建 ASSET + 瘦身 TOPIC + 迁移脚本
[v3 Step 6.1] 重写小哨/小编/小文 prompt（含 few-shot 和测试）
[v3 Step 10] 端到端冒烟通过 + bootstrap v3 升级
[v3 Final] 自主冲刺完成：9 Agent 端到端通过 + 11 Bug 修复
```

### 7.3 Push 节奏

**每个 Step 完成立即 push**。不要积累多个 Step 一次 push（万一中途出错，已完成的进度有保障）。

### 7.4 .gitignore 检查

确保以下文件 **不被 push**：
- `.env`（含密钥）
- `*.log`（日志）
- `__pycache__/`
- `.idea/`、`.vscode/`
- 任何含 token / secret 的临时文件

如发现误 push 密钥：
1. 立即 revert：`git revert HEAD`
2. 在 worklog 标记，**告诉 ZQ 需要换 key**
3. 不要试图 `git push --force` 改写历史

---

## 八、验收标准（自检清单）

### 8.1 代码层验收

```
□ 9 个 Agent prompt 文件 + 2 个 shared 文件（koc_persona + chinese_hooks）+ 1 个 parser 文件 全部就位
□ 每个 prompt 文件含 SYSTEM_PROMPT / USER_TEMPLATE / FEW_SHOT_EXAMPLES / build_messages
□ build_messages 强制要求 koc 非空（v3 修复 Bug 1）
□ parse_thinking_answer 提取 <thinking> + <answer> 双标签
□ invoke_with_retry 最大 3 次重试
□ production_sync 节点存在且测试通过
□ ASSET schema 23 字段全部正确
□ TOPIC schema 瘦身到 13 字段
□ LangGraph builder 含审改循环条件边（max_revisions=3）
```

### 8.2 测试层验收

```
□ tests/prompts/ 下 9 个 Agent 各有 test_xxx_prompt.py
□ 每个 prompt 测试至少 3 个用例（few_shot_consistency + pass + edge）
□ tests/bug_fixes/ 下 9 个 bug 修复测试全 pass
□ tests/graph/test_production_sync.py 通过
□ tests/utils/test_llm_parser.py 通过
```

### 8.3 飞书产物验收

```
□ 飞书 Base 9 张表全部创建
□ ASSET 表 23 字段，TOPIC 表 13 字段
□ 飞书云空间 NewsAI产物/ 5 子文件夹
□ 1 条选题完整端到端 = 9 个飞书云文档
□ TOPIC.选题状态 = "已发布"
□ ASSET 6 状态字段都切换过
□ 审改文档可见累积式追加
□ 5 个分发文档内容差异化（不是粘贴）
```

### 8.4 Git 验收

```
□ 至少 12 个 commit（每 Step 1+）
□ commit 消息规范（[v3 Step X] 格式）
□ 最新 commit 已 push 到 origin/main
□ .env 没被 push
□ worklog.md 完整记录每个 Step
```

---

## 九、不要做的事

最后强调，这些事**绝对不要做**：

1. ❌ 不要回头读 v1 文档（4 份 _v1_deprecated）
2. ❌ 不要修改 v3 设计文档（Prompts_v3.md / Tables_schema_v2.md 等）
3. ❌ 不要"为了快"跳过测试
4. ❌ 不要并行做多个 Step（除明确标注可并行的）
5. ❌ 不要等 ZQ 拍板（v3 文档已经是最终决议）
6. ❌ 不要 `git push --force`
7. ❌ 不要 commit 含 `.env`
8. ❌ 不要在端到端失败时"假装通过"（worklog 标记真实状态）
9. ❌ 不要修改 KOC 人设的字段（KOC-001 是固定基线）
10. ❌ 不要在选题中嵌入 KOC 没有的 "焦虑话术"——即使是测试数据也不要

---

## 十、开始

**第一步**：通读这份执行指南到这里 → 在 worklog 写一段确认：

```markdown
## YYYY-MM-DD HH:MM · 自主冲刺开始

我已通读 ClaudeCode_Execution_Prompt.md，理解：
- 12 个 Step 的执行顺序
- worklog 写作规范
- 出错处置流程
- Git push 规则
- 验收标准

现在开始 Step 0：环境检查。
```

**然后**：按 Step 0 → Step 12 顺序执行。

**祝你顺利。屌就完事了。** 🚀

---

*执行指南 v1.0 · ZQ 沉淀于 2026-05-04 SGT*
