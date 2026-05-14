# NewsAI 使用手册

> 本文档覆盖 NewsAI 从初始化到日常使用的完整操作指南。v3.1 版本。

---

## 目录

1. [启动项目](#1-启动项目)
2. [创建表格](#2-创建表格)
3. [更改预设内容](#3-更改预设内容)
4. [更改 Agent Prompt](#4-更改-agent-prompt)
5. [启动完整流程](#5-启动完整流程)
6. [单独启动某个 Agent](#6-单独启动某个-agent)
7. [小数复盘流程](#7-小数复盘流程)

---

## 1. 启动项目

### 1.1 环境要求

- Python 3.11+
- 飞书企业账号（用于 Bitable 存储）
- 火山方舟 API Key（用于 LLM 调用）

### 1.2 安装依赖

```bash
cd D:\Code\NewsAI
pip install -e .
```

### 1.3 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env` 文件，填入以下密钥：

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `LARK_APP_ID` | 飞书应用 ID | 飞书开放平台 → 应用管理 |
| `LARK_APP_SECRET` | 飞书应用密钥 | 同上 |
| `LARK_BASE_APP_TOKEN` | 多维表格 Token | Base 链接中截取 |
| `ARK_API_KEY` | 火山方舟 API Key | 火山引擎控制台 |

### 1.4 初始化（一键建表 + 种子数据）

```bash
python bootstrap.py
```

输出示例：

```
=== NewsAI Bootstrap ===
[0/4] 检查环境变量... 通过
[1/4] 验证连接飞书Base... 成功! 连接 8 表
[2/4] 创建/验证表... 完成
  信源配置        : 7 条种子数据
  KOC人设        : 1 条种子数据
  Agent花名册    : 9 条种子数据
[4/4] 生成摘要... 完成

Base链接: https://base.feishu.cn/xxx
```

---

## 2. 创建表格

### 2.1 自动创建

`bootstrap.py` 会自动创建 **8 张表**：

| # | 表名 | 用途 | ID前缀 |
|---|------|------|--------|
| 1 | **信源配置** | 7个信息源的配置参数 | SRC |
| 2 | **热帖库** | 小哨采集的原始热帖 | TREND |
| 3 | **选题库** | 小编筛选后的选题方案 | TOPIC |
| 4 | **内容资产库** | 生产流水线 + 所有文档链接 | ASSET |
| 5 | **数据库** | 小数的数据分析结果 | DATA |
| 6 | **KOC人设** | 虚拟KOC的人设设定 | KOC |
| 7 | **Agent花名册** | 9个Agent的档案信息 | EMP |
| 8 | **Agent协作日志** | 执行轨迹记录 | LOG |

### 2.2 手动检查表状态

```bash
python scripts/check_base_status.py
```

需要设置 `PYTHONPATH`：

```bash
# PowerShell
$env:PYTHONPATH = "."; python scripts/check_base_status.py

# Bash (Linux/Mac)
PYTHONPATH=. python scripts/check_base_status.py
```

### 2.3 重新创建表格

如果表结构需要更新（如新增字段）：

1. 修改 `feishu_adapter/base/tables.py` 中的字段定义
2. 在飞书 Base 中手动删除旧表
3. 重新运行 `python bootstrap.py`

---

## 3. 更改预设内容

### 3.1 更改 KOC 人设

**方式一：直接修改代码（推荐，可版本控制）**

编辑 `feishu_adapter/base/tables.py` 中的 `KOC_SEED_DATA`：

```python
KOC_SEED_DATA = [
    {
        "id": "KOC-001",
        "账号名": "学AI的刘同学",      # ← 修改这里
        "一句话定位": "...",           # ← 修改这里
        "领域": ["AI 资讯", "AI 工具"], # ← 修改这里
        "语气": "...",                 # ← 修改这里
        # ... 其他字段
    }
]
```

**方式二：直接在飞书 Base 中修改**

登录飞书 → 打开 NewsAI Base → 找到 **KOC人设** 表 → 直接编辑对应字段。

> 注意：方式二修改后不会被代码记录，下次 bootstrap 会覆盖。如需持久化，请同时修改 `tables.py`。

**字段映射说明**：

| 字段 | 影响的 Agent |
|------|-------------|
| `领域`、`偏好选题类型` | 小哨（决定监控哪些信息源） |
| `一句话定位`、`语气`、`受众痛点` | 小编、小文、小图、小播 |
| `禁区话题`、`不想成为的样子` | 小审（审查红线） |
| `主战场平台`、`发布频率` | 小发（分发策略） |
| `目标受众`、`受众期待` | 小数（数据复盘对照） |

### 3.2 更改 Agent 花名册

编辑 `feishu_adapter/base/tables.py` 中的 `EMP_SEED_DATA`：

```python
EMP_SEED_DATA = [
    {
        "id": "EMP-001",
        "花名": "小哨",
        "英文代号": "TrendScout",
        "部门": "信息组",
        "调用模型": "Doubao-pro-32k",  # ← 可修改模型
        # ...
    },
    # ...
]
```

### 3.3 更改信源配置

编辑 `feishu_adapter/base/tables.py` 中的 `SOURCE_CONFIG_SEED_DATA`，或修改 `mock_data/` 目录下的 JSON 文件：

```
mock_data/
├── arxiv_papers.json      # arXiv 论文
├── hackernews_hot.json    # HN 热帖
├── github_trending.json   # GitHub 趋势
├── reddit_posts.json      # Reddit 帖子
├── x_hot.json             # X(Twitter) 热帖
├── xiaohongshu_hot.json   # 小红书
└── douyin_hot.json        # 抖音
```

修改后重新运行 `python bootstrap.py` 生效。

---

## 4. 更改 Agent Prompt

### 4.1 Agent System Prompt（角色定义）

每个 Agent 的 System Prompt 定义在其对应的 Python 文件中：

| Agent | 文件路径 | System Prompt 变量名 |
|-------|----------|---------------------|
| 小哨 | `core/agents/trend_scout.py` | `SYSTEM_PROMPT` |
| 小编 | `core/agents/topic_curator.py` | `SYSTEM_PROMPT` |
| 小文 | `core/agents/content_writer.py` | `SYSTEM_PROMPT` |
| 小图 | `core/agents/visual_designer.py` | `SYSTEM_PROMPT` |
| 小播 | `core/agents/script_writer.py` | `SYSTEM_PROMPT` |
| 小审 | `core/agents/reviewer.py` | `SYSTEM_PROMPT` |
| 小改 | `core/agents/editor.py` | `SYSTEM_PROMPT` |
| 小发 | `core/agents/distributor.py` | `SYSTEM_PROMPT_STEP1` / `SYSTEM_PROMPT_STEP2` |
| 小数 | `core/agents/analyst.py` | `SYSTEM_PROMPT` |

**修改示例**（小审的审查标准）：

```python
# core/agents/reviewer.py
class ReviewerAgent(BaseAgent):
    SYSTEM_PROMPT = """\
<role>
你是「小审 Reviewer」，NewsAI 编辑部的审核员...
# ← 在这里修改角色定义、审查标准
</role>
"""
```

### 4.2 共享 Prompt 模块

| 模块 | 文件路径 | 用途 |
|------|----------|------|
| KOC 人设渲染 | `core/prompts/shared/koc_persona.py` | 所有 Agent 读取 KOC 人设 |
| 中文爆款基因库 | `core/prompts/shared/chinese_hooks.py` | 中文内容爆款公式 |

### 4.3 User Prompt（动态构建）

每个 Agent 的 `_build_user_prompt()` 方法负责拼接具体的任务 prompt：

```python
# core/agents/content_writer.py
class ContentWriterAgent(BaseAgent):
    def _build_user_prompt(self, koc_block, topic, trends):
        # ← 在这里修改 prompt 模板
        return f"""\
{koc_block}
<input>
选题标题：{topic.get('选题标题', '')}
# ...
</input>
"""
```

### 4.4 Prompt 查看工具

```bash
python scripts/show_prompts.py
```

显示所有 Agent 的 Prompt 方法名和预览（前300字符）。

---

## 5. 启动完整流程

### 5.1 跑一轮完整流程

```bash
python run.py --once
```

流程顺序（主流程）：

```
小哨(采集) → 小编(策划) → 小文(长文)
                                      ↓
                          [并行] 小图(配图) + 小播(脚本)
                                      ↓
                          production_sync（3状态全完成才放行）
                                      ↓
                          小审(审查) ←→ 小改(修改) [最多3轮]
                                      ↓
                          小发(分发) → END
```

> 小数（复盘分析）已从主流程拆分，改为独立运行。详见 [第7节](#7-小数复盘流程)。

### 5.2 指定选题运行

```bash
python run.py --once --topic TOPIC-20260513-001
```

### 5.3 查看运行日志

```bash
# 查看最新日志
cat logs/full_run_*.log

# PowerShell
cat logs\full_run_*.log
```

---

## 6. 单独启动某个 Agent

### 6.1 CLI 方式

```bash
python run.py --agent trend      # 小哨：信息采集
python run.py --agent topic      # 小编：选题策划
python run.py --agent content    # 小文：内容撰写
python run.py --agent visual     # 小图：视觉设计
python run.py --agent script     # 小播：脚本撰写
python run.py --agent review     # 小审：审核
python run.py --agent edit       # 小改：修改
python run.py --agent distribute # 小发：分发
python run.py --agent analyze    # 小数：分析
```

### 6.2 Python 导入方式（调试用）

```python
from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.agents.trend_scout import TrendScoutAgent

storage = FeishuStorage()
llm = get_llm()
agent = TrendScoutAgent(storage, llm)
result = agent.execute({})
print(result)
```

其他 Agent 的类名对照：

| 花名 | 类名 | 模块路径 |
|------|------|----------|
| 小哨 | `TrendScoutAgent` | `core.agents.trend_scout` |
| 小编 | `TopicCuratorAgent` | `core.agents.topic_curator` |
| 小文 | `ContentWriterAgent` | `core.agents.content_writer` |
| 小图 | `VisualDesignerAgent` | `core.agents.visual_designer` |
| 小播 | `ScriptWriterAgent` | `core.agents.script_writer` |
| 小审 | `ReviewerAgent` | `core.agents.reviewer` |
| 小改 | `EditorAgent` | `core.agents.editor` |
| 小发 | `DistributorAgent` | `core.agents.distributor` |
| 小数 | `AnalystAgent` | `core.agents.analyst` |

### 6.3 带上下文运行

```python
from feishu_adapter.feishu_storage import FeishuStorage
from core.llm.client import get_llm
from core.agents.reviewer import ReviewerAgent

storage = FeishuStorage()
llm = get_llm()
agent = ReviewerAgent(storage, llm)

# 传入 topic_id 和 asset_id，Agent 会直接读取对应记录
result = agent.execute({
    "topic_id": "TOPIC-20260513-001",
    "asset_id": "ASSET-20260513-001",
})
print(result)
```

---

## 7. 小数复盘流程

小数（数据复盘 Agent）已从主流程拆分，独立运行。数据收集和复盘通常在内容分发之后的第二天进行。

### 7.1 一键运行（推荐）

```bash
# PowerShell
$env:PYTHONPATH = "."; python scripts/run_analyst.py
```

该脚本会自动完成两步：
1. 运行 `mock_data_demo.py` 生成/收集数据到 **数据库** 表
2. 运行 `python run.py --agent analyze` 启动 小数 做深度复盘分析

### 7.2 分步运行

如果你想分步执行（例如使用真实数据而非 mock 数据）：

**Step 1 — 准备数据**

确保 **数据库** 表中至少有一条记录，且 **数据状态** 为 `待分析`。

如需用 LLM 生成模拟数据：

```bash
$env:PYTHONPATH = "."; python scripts/mock_data_demo.py
```

**Step 2 — 启动 小数 分析**

```bash
python run.py --agent analyze
```

### 7.3 前置条件

- 内容资产库中至少有一条资产的 **分发状态** 为 `已生成` 或 `已完成`
- 数据库表中至少有一条记录的 **数据状态** 为 `待分析`

### 7.4 输出

小数会产出 **3 个产物**：

| 产物 | 存储位置 | 说明 |
|------|----------|------|
| 经验总结文档 | 飞书云文档 | 可沉淀经验 + 选题策略优化建议 |
| 数据分析文档 | 飞书云文档 | 各平台数据表格 + 数据与内容关联分析 |
| 数据库更新 | Bitable 数据库表 | 经验文档链接、数据分析文档链接、数据状态→`已分析` |

### 7.5 分析维度

- **数据与选题关联**：哪些数据印证了选题判断？哪些偏离了预期？
- **平台差异分析**：为什么某些平台表现好/差？
- **内容质量归因**：数据表现与文案/配图/视频脚本质量的关联
- **可沉淀经验**：3-5 条可复用的经验
- **选题策略优化**：基于数据反馈的下一期建议

---

## 附录：常见问题

### 中文乱码

```bash
# PowerShell
chcp 65001
$env:PYTHONIOENCODING = "utf-8"
```

### 模块导入错误

```bash
# 确保在项目根目录，并设置 PYTHONPATH
cd D:\Code\NewsAI
$env:PYTHONPATH = "."
```

### 飞书权限错误 (91403)

1. 登录飞书开放平台
2. 进入应用管理 → 权限管理
3. 添加权限：`bitable:record`（读取/写入/更新记录）
4. 重新获取 app_token

### 清理数据重新来过

```bash
# 在飞书 Base 中手动删除所有表记录
# 然后重新初始化
python bootstrap.py
```

---

*NewsAI v3.1 使用手册 · 最后更新：2026-05-14*
