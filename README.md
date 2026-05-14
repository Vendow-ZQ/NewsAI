# NewsAI - AI 虚拟新闻编辑部

**飞书 AI 校园挑战赛参赛作品**

> 跑在飞书多维表格上的 AI 虚拟新闻编辑部 —— 9 个 AI Agent 7×24 自动采集全球 AI 信息源，转译为中文爆款内容。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.x-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![飞书](https://img.shields.io/badge/飞书-Bitable-green.svg)](https://open.feishu.cn/)

---

## 一句话介绍

**9 个 AI Agent 组成虚拟新闻编辑部**，自动完成信息采集 → 选题策划 → 内容生产（图文视频并行）→ 审核修改（最多3轮循环）→ 多平台分发的全流程，所有产物存储在飞书多维表格，全程可追溯、可接管、可学习。小数（数据复盘）可独立运行，通常在分发次日执行。

---

## 核心特性

### 1. 9 人虚拟编辑部

基于真实编辑部组织架构，4 部门 + 1 独立设计：

```
总裁办（KOC 本人）
    │
    ├── 信息组 · 小哨 TrendScout     (EMP-001) · 信息官
    │
    ├── 决策组 · 小编 TopicCurator   (EMP-002) · 选题总编
    │
    ├── 生产组（3人并行）
    │   ├── 小文 ContentWriter      (EMP-003) · 文字编辑
    │   ├── 小图 VisualDesigner     (EMP-004) · 视觉设计师
    │   └── 小播 ScriptWriter       (EMP-005) · 短视频编剧
    │
    ├── 治理组（审改循环）
    │   ├── 小审 Reviewer           (EMP-006) · 审核员
    │   └── 小改 Editor             (EMP-007) · 修改专员
    │
    ├── 分发组 · 小发 Distributor    (EMP-008) · 分发策略师
    │
    └── 独立复盘组 · 小数 Analyst    (EMP-009) · 数据分析师
```

### 2. LangGraph 状态机编排（v3.1）

```
小哨(采集) → 小编(策划) → 小文(长文源稿)
                                     ↓
                         [并行] 小图(配图) + 小播(脚本)
                                     ↓
                         production_sync（3状态全完成才放行）
                                     ↓
                         小审(审查) ←→ 小改(修改)  [最多3轮审改循环]
                                     ↓
                         小发(分发) → END
```

**v3.1 关键改进**：
- **串行+翻译模式**：小编 → 小文（先写长文源稿），小文完成后 fan-out 到小图+小播
- **production_sync 阻断**：3个生产状态全为"已完成"才进入审改，防止审改提前启动
- **审改循环**：小审-小改最多3轮，第3轮强制通过
- **小数拆分**：数据分析（小数）从主流程拆分为独立脚本 `scripts/run_analyst.py`，分发次日运行
- **状态驱动**：Bitable 表状态流转，全程可追溯

### 3. Bitable-Centric 混合架构（v3.0）

状态与元数据存储在飞书多维表格，长文本产物存储在飞书云文档，Bitable 留存文档链接：

| 产物类型 | 存储位置 | 格式 |
|---------|---------|------|
| 帖子内容 | 内容资产库.文案文档链接 | 飞书文档 |
| 图素材池 | 内容资产库.图片提示词文档链接 | 飞书文档 |
| 视频脚本 | 内容资产库.视频脚本文档链接 | 飞书文档 |
| 审改记录 | 内容资产库.审改文档链接 | 飞书文档（累积追加） |
| 分发计划 | 内容资产库.分发计划JSON | JSON |
| 协作日志 | Agent协作日志表 | 结构化记录 |

### 4. 工程级 Prompt 设计

基于 Anthropic Prompt Engineering Best Practices (2026) + The Prompt Report 最佳实践：

- **XML结构化分区**：role/context/rules/examples/self_check 标签
- **Few-Shot示例**：每个Agent 3+示例（正例+反例+边界例）
- **人设翻译**：抽象KOC人设→可执行标准（✅会做/❌不做）
- **Thinking块**：强制CoT思考，提升推理准确率40%+
- **输出契约**：严格JSON schema + 字数上限 + 格式锚点
- **自检清单**：输出前LLM自我review，提升质量15-20%

**Prompt位置**：
- Agent System Prompt：`core/agents/{agent}.py` 中的 `SYSTEM_PROMPT`
- KOC人设模块：`core/prompts/shared/koc_persona.py`
- 中文爆款基因库：`core/prompts/shared/chinese_hooks.py`
- 完整Prompt参考：`docs/AGENT_PROMPTS_MASTER.md`（2556行工程文档）

---

## 快速开始

### 环境准备

```bash
# 1. 克隆仓库
git clone https://github.com/Vendow-ZQ/NewsAI.git
cd NewsAI

# 2. 安装依赖
pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入以下密钥：
#   LARK_APP_ID, LARK_APP_SECRET     (飞书开放平台)
#   LARK_BASE_APP_TOKEN              (飞书Base URL中的token)
#   ARK_API_KEY                      (火山方舟)
```

### 一键初始化

```bash
python bootstrap.py
```

功能：
- ✅ 检查环境变量
- ✅ 连接飞书Bitable
- ✅ 创建8张表（信源配置/热帖库/选题库/内容资产库/数据库/KOC人设/Agent花名册/Agent协作日志）
- ✅ 插入种子数据（7信源+1KOC+9Agent花名册）
- ✅ 打印Base链接

### 运行

```bash
# 跑一轮完整流程
python run.py --once

# 指定选题运行
python run.py --once --topic TOPIC-20260513-001

# 单独调试某个Agent
python run.py --agent trend      # 小哨
python run.py --agent topic      # 小编
python run.py --agent content    # 小文
python run.py --agent visual     # 小图
python run.py --agent script     # 小播
python run.py --agent review     # 小审
python run.py --agent edit       # 小改
python run.py --agent distribute # 小发
python run.py --agent analyze    # 小数

# 小数复盘流程（独立运行，通常在分发次日执行）
python scripts/run_analyst.py

# 或分步运行：
# python scripts/mock_data_demo.py  # Step 1: 生成/收集数据
# python run.py --agent analyze     # Step 2: 启动小数分析
```

---

## 项目结构

```
NewsAI/
├── 核心入口
│   ├── bootstrap.py          # 一键初始化（建表+种子数据）
│   ├── run.py                # 主入口：完整流程/单Agent调试
│   └── pyproject.toml        # 依赖配置
│
├── 核心业务层 (core/)
│   ├── agents/               # 9个Agent实现（v3.0）
│   │   ├── base.py           # BaseAgent抽象基类（模板方法模式）
│   │   ├── trend_scout.py    # 小哨 - 信息采集
│   │   ├── topic_curator.py  # 小编 - 选题策划
│   │   ├── content_writer.py # 小文 - 文字编辑
│   │   ├── visual_designer.py# 小图 - 视觉设计
│   │   ├── script_writer.py  # 小播 - 短视频编剧
│   │   ├── reviewer.py       # 小审 - 审核员
│   │   ├── editor.py         # 小改 - 修改专员
│   │   ├── distributor.py    # 小发 - 分发策略
│   │   └── analyst.py        # 小数 - 数据分析师
│   ├── graph/                # LangGraph编排
│   │   ├── builder.py        # 图构建工厂（流程定义）
│   │   ├── state.py          # 共享State（支持并发合并）
│   │   ├── nodes.py          # 9个节点包装器
│   │   └── edges.py          # 审改循环条件边
│   ├── prompts/shared/       # 共享Prompt模块
│   │   ├── koc_persona.py    # KOC人设渲染
│   │   └── chinese_hooks.py  # 中文爆款基因库
│   ├── sources/              # 信息源采集（7个mock源）
│   ├── storage/              # 存储接口
│   └── utils/                # 工具类（FeishuBaseManager等）
│
├── 飞书适配层 (feishu_adapter/)
│   ├── feishu_storage.py     # Storage接口实现
│   └── base/
│       ├── tables.py         # 8张表Schema+种子数据
│       └── id_mapping.py     # 业务ID↔record_id映射
│
├── scripts/
│   ├── archive/              # 旧版运行脚本归档
│   ├── verification/         # 端到端验证脚本
│   │   ├── e2e_verify_v2.py  # v3.1 完整流程验证
│   │   └── e2e_verify.py     # v3.0 验证脚本
│   ├── check_base_status.py  # Base状态诊断
│   ├── show_prompts.py       # 查看所有Agent Prompt
│   ├── mock_data_demo.py     # 数据库 mock 数据生成（小数前置脚本）
│   └── run_analyst.py        # 小数复盘一键脚本（mock_data + analyze）
│
├── tests/                    # 测试文件
├── reports/                  # 测试报告（e2e_report_*.json）
├── logs/                     # 运行日志
└── data/                     # 数据文件（.id_mapping.json）
│
└── 文档 (docs/)
    ├── Final_Prompts.md           # 完整Prompt工程文档 ⭐
    ├── Agent_roster_v2.md         # 9位虚拟员工档案 ⭐
    ├── Documents_design_v2.md     # 内容产物设计 ⭐
    ├── NewsAI_project_v2.md       # 项目概述 ⭐
    ├── Tables_schema_v2.md        # 表结构设计 ⭐
    ├── KOC_persona.md             # KOC人设
    └── archive/                   # 历史文档归档
        ├── AGENT_PROMPTS.md       # 早期简单Prompt
        ├── SOP_v2.md              # 开发过程记录
        └── ...

其他根目录文件：
├── QUICKSTART.md           # 快速开始指南
├── worklog.md              # 完整工作日志
├── .env.example            # 环境变量模板
└── .gitignore              # Git忽略配置
```

---

## 核心流程详解

### Step 1: 信息采集（小哨）

- 从 7 个 mock 文件各抽 3 条 = **21条热帖**
- LLM 统一打分（热度评分 0-1，内容质量高/中/低）
- 打主题标签（新模型发布/新工具发布/行业八卦等9类）
- 写入**热帖库**（状态="待选"）

### Step 2: 选题策划（小编）

- 读取全部 21 条热帖
- **3关筛查**：领域白名单 → 禁区话题 → 爆点可挖掘性
- **5维度爆点拆解**：情绪钩子/知识增量/身份代入/反差/时效
- 输出 **3条候选选题**（按优先级排序）
- 自动选中优先级最高的，创建 **ASSET 内容资产**
- 写入**选题库**（状态="已选中"）

### Step 3: 内容生产（并行）

**小文**（文字编辑）：
- 读选题 + 关联热帖原文
- 写 **1 篇长文源稿**（1000-3000字，不分平台）
- 至少 5 个 `[配图N: 描述]` 占位
- 创建飞书文档，更新 ASSET.文案状态="已完成"

**小图**（视觉设计师）：
- 读选题 + 小文长文全文
- 产出 **5-8 张图素材池**（文字卡片/信息图/AI画面）
- 每张图标注适用平台（小红书/公众号/抖音等）
- 创建飞书文档，更新 ASSET.配图状态="已完成"

**小播**（短视频编剧）：
- 读选题 + 小文长文全文
- 写 **1 个主视频脚本**（1-3分钟）
- 包含：钩子开场/核心内容/CTA/镜头清单/BGM建议
- 创建飞书文档，更新 ASSET.视频状态="已完成"

### Step 4: 审改循环（小审 ↔ 小改）

**小审**（审核员）：
- 审查 3 件资产（长文 + 图素材池 + 视频脚本）
- **4维度审查**：事实核查/风险词扫描/人设一致性/平台合规
- 判定：pass → 进入分发 / needs_revision → 进入小改

**小改**（修改专员）：
- 读审改文档（含小审的issues清单）
- 逐条精确修改，输出 **changelog（diff格式）**
- 更新审改文档，等待再审

**循环机制**：
- 最多 3 轮
- 第 3 轮强制通过，保留遗留问题清单
- 连续 dispute 3 次 → 标记为"卡死"，需人工介入

### Step 5: 分发策略（小发）

- 读取通过审改的 3 件资产终稿
- **步骤1**：拆分为 **5 平台版本**（公众号/小红书/抖音/视频号/B站）
  - 每平台：专属文案 + 配图绑定 + 视频剪辑指引
- **步骤2**：制定完整分发计划
  - 5 平台发布时间表（错峰 + 黄金时段）
  - 受众标签 + 预期效果 + 风险提示
- 创建 5 个飞书分发文档
- 更新 TOPIC.选题状态="已发布"

### Step 6: 数据分析（小数）—— 独立运行

小数已从主流程拆分，通常在内容分发次日执行。

**一键运行**：
```bash
python scripts/run_analyst.py
```
该脚本先运行 `mock_data_demo.py` 生成/收集数据，再启动 小数 Agent 做复盘。

**分步运行**：
```bash
# Step 1: 生成/收集数据
python scripts/mock_data_demo.py

# Step 2: 启动 小数 分析
python run.py --agent analyze
```

**分析内容**：
- 读取 **数据库** 表中最新记录（数据状态="待分析"）
- 读取关联选题、资产、分发文档摘要
- LLM 深度分析：
  - 数据与选题策划的关联分析
  - 各平台差异原因分析
  - 内容质量归因
  - 3-5 条可沉淀经验
  - 选题策略优化建议
- 产出：
  - **经验总结文档**（飞书云文档）
  - **数据分析文档**（飞书云文档）
- 更新数据库表：数据状态→"已分析"，记录文档链接

---

## 8 张 Bitable 表

| 表名 | 用途 | 记录数 |
|------|------|--------|
| **信源配置** | 7个信息源的配置 | 7条（种子） |
| **热帖库** | 小哨采集的原始内容（含原文链接、原文摘要） | 21条/轮 |
| **选题库** | 小编筛选后的选题方案（含原文摘要、数据回流ID） | 3条/轮 |
| **内容资产库** | 生产流水线+所有文档链接（文案/配图/视频/审改/分发） | 1条/选题 |
| **数据库** | 小数的数据分析结果（经验文档+分析文档链接） | 1条/选题 |
| **KOC人设** | 虚拟KOC的人设设定 | 1条（种子） |
| **Agent花名册** | 9个Agent的档案 | 9条（种子） |
| **Agent协作日志** | 执行轨迹（开始时间/结束时间/耗时秒数） | 10+条/轮 |

---

## 关键文档索引

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [docs/AGENT_PROMPTS_MASTER.md](docs/AGENT_PROMPTS_MASTER.md) | 所有Agent的完整System Prompt（2556行工程文档） | ⭐⭐⭐⭐⭐ |
| [docs/AGENT_ROSTER.md](docs/AGENT_ROSTER.md) | 9位虚拟员工档案+组织架构 | ⭐⭐⭐⭐⭐ |
| [docs/CONTENT_DESIGN.md](docs/CONTENT_DESIGN.md) | 4类内容产物设计（Bitable+云文档混合架构） | ⭐⭐⭐⭐⭐ |
| [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | 项目概述+商业模式+核心差异化 | ⭐⭐⭐⭐⭐ |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | 8张表的字段定义+样例数据 | ⭐⭐⭐⭐ |
| [docs/KOC_PERSONA.md](docs/KOC_PERSONA.md) | KOC「学AI的刘同学」人设 | ⭐⭐⭐⭐ |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构、数据流、设计模式详解 | ⭐⭐⭐⭐ |
| [worklog.md](worklog.md) | 完整开发日志（2026-05-03至今） | ⭐⭐⭐ |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始指南 | ⭐⭐⭐ |

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 编排引擎 | **LangGraph** | 状态图驱动9 Agent协作 |
| LLM | **Doubao 2.0** (火山方舟) | 通过OpenAI协议调用 |
| 存储 | **飞书 Bitable** | 8张多维表格，无外部数据库 |
| SDK | lark-oapi + langchain-openai | 飞书+LLM双端对接 |
| 工作流 | 状态机驱动 | Bitable状态流转而非内存状态 |

---

## 最近更新

### 2026-05-14 v3.1 修复：小数拆分 + set_permissions 修复

- 🔀 **小数从主流程拆分**：主流程在小发写入协作日志后结束，小数改为独立脚本 `scripts/run_analyst.py`（先 mock_data + 后 analyze），适配"数据收集在次日"的真实业务场景
- 🔧 **set_permissions 修复**：移除 JSON body 中的非法字段 `"type": "public"`，改为 URL query parameter `?type=docx`，解决所有 Agent 文档权限设置报 `field validation failed` 的问题
- 🔧 **storage.update 失败可见**：当 `update_record` 返回 False 时打印 `[警告] 更新记录失败` 日志，避免静默失败

### 2026-05-13 v3.1 全流程修复与字段完善

- 🔧 **production_sync 阻断修复**：RuntimeError 被自身 try-except 捕获导致审改提前启动 → 将检查逻辑移出 try-except，真正阻断未完成的流程
- 🔧 **文档读取修复**：`elements[0].text.content` → `elements[0].text_run.content`，修正 block 属性名和 block_type 常量
- 🔧 **批量写入修复**：飞书 API 单次 block 上限为 50（非 100），`batch_size` 修正
- 📋 **数据字段完善**：热帖库补充 `原文链接`、选题库新增 `原文摘要`、Agent协作日志任务类型明确枚举
- 📊 **小数重构**：从数据库表读取真实数据，生成经验文档 + 数据分析文档
- 🧪 **端到端验证**：新增 `scripts/verification/e2e_verify_v2.py`，12min 全链路跑通

### 2026-05-12 文件夹结构整理

- 📁 重构文件夹结构，43个文件归位
- 📄 文档文件 → docs/
- 🧪 测试文件 → tests/
- 📊 测试报告 → reports/
- 💾 数据文件 → data/
- 📝 归档脚本 → scripts/archive/
- 🗑️ 删除空文件 (EOF, PYEOF)

---

## 作者

**ZQ (Vendow)** - 清华大学 SIGS · 未来人居研究院

- GitHub: [@Vendow-ZQ](https://github.com/Vendow-ZQ)
- 赛事：飞书 AI 校园挑战赛

---

*NewsAI - AI虚拟新闻编辑部 · 把硅谷的 AI 热点，连夜翻译成小红书的爆款。*
