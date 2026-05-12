# NewsAI 项目分析与文档整理建议

## 一、项目结构分析

### 1.1 核心架构

```
NewsAI/
├── 核心入口
│   ├── bootstrap.py          # 项目初始化（建表+种子数据）
│   └── run.py                # 主运行入口
│
├── 核心业务层 (core/)
│   ├── agents/               # 9个Agent实现
│   │   ├── base.py           # BaseAgent基类（模板方法模式）
│   │   ├── trend_scout.py    # 小哨 EMP-001 · 信息官
│   │   ├── topic_curator.py  # 小编 EMP-002 · 选题总编
│   │   ├── content_writer.py # 小文 EMP-003 · 文字编辑
│   │   ├── visual_designer.py# 小图 EMP-004 · 视觉设计师
│   │   ├── script_writer.py  # 小播 EMP-005 · 短视频编剧
│   │   ├── reviewer.py       # 小审 EMP-006 · 审核员
│   │   ├── editor.py         # 小改 EMP-007 · 修改专员
│   │   ├── distributor.py    # 小发 EMP-008 · 分发策略师
│   │   └── analyst.py        # 小数 EMP-009 · 数据分析师
│   ├── graph/                # LangGraph编排
│   │   ├── builder.py        # 图构建工厂
│   │   ├── state.py          # 共享State
│   │   ├── nodes.py          # 节点包装器
│   │   └── edges.py          # 审改循环条件边
│   ├── prompts/shared/       # 共享Prompt模块
│   │   ├── koc_persona.py    # KOC人设渲染
│   │   └── chinese_hooks.py  # 中文爆款基因库
│   ├── sources/              # 信息源采集（7个mock源）
│   ├── storage/              # 存储接口
│   └── utils/                # 工具类
│
├── 飞书适配层 (feishu_adapter/)
│   ├── feishu_storage.py     # Storage接口实现
│   ├── base/tables.py        # 表Schema定义
│   └── docs/                 # 飞书文档操作
│
└── 归档目录
    ├── scripts/archive/      # 旧版运行脚本
    ├── tests/                # 测试文件
    ├── reports/              # 测试报告
    └── logs/                 # 运行日志
```

### 1.2 核心流程

```
小哨(采集21条) → 小编(策划3条) → [并行] 小文(长文) + 小图(5-8张图) + 小播(脚本)
                                                          ↓
                                    小审(审查) ←→ 小改(修改)  [最多3轮审改循环]
                                                          ↓
                                    小发(5平台分发) → 小数(数据分析) → END
```

### 1.3 Prompt位置

| 类型 | 位置 | 说明 |
|------|------|------|
| Agent System Prompt | `core/agents/{agent}.py` | 每个Agent类中的 `SYSTEM_PROMPT` 类变量 |
| KOC人设 | `core/prompts/shared/koc_persona.py` | `render_koc_block()` 函数 |
| 中文爆款基因 | `core/prompts/shared/chinese_hooks.py` | `CHINESE_HOOKS_BLOCK` 常量 |
| 完整Prompt参考 | `docs/Final_Prompts.md` | v2.0工程级Prompt汇总（2556行） |

---

## 二、Docs文档分析

### 2.1 现有文档清单

| 文档 | 行数 | 类型 | 价值评估 | 建议 |
|------|------|------|----------|------|
| **Final_Prompts.md** | 2556 | 技术参考 | ⭐⭐⭐⭐⭐ 最完整的Prompt文档 | **保留** - 所有Agent的完整Prompt |
| **Agent_roster_v2.md** | 666 | 架构文档 | ⭐⭐⭐⭐⭐ 组织架构+职责 | **保留** - 虚拟员工档案 |
| **Documents_design_v2.md** | 696 | 架构文档 | ⭐⭐⭐⭐⭐ 内容产物设计 | **保留** - Bitable-only架构核心 |
| **NewsAI_project_v2.md** | 405 | 项目概述 | ⭐⭐⭐⭐⭐ 项目简介 | **保留并更新** - 参赛主文档 |
| **Tables_schema_v2.md** | 464 | 技术规范 | ⭐⭐⭐⭐ 表结构设计 | **保留** - 7张表Schema |
| **KOC_persona.md** | 306 | 人设文档 | ⭐⭐⭐⭐ KOC人设 | **保留** - 刘同学人设 |
| **AGENT_PROMPTS.md** | 534 | 技术参考 | ⭐⭐⭐ 早期简单Prompt | **归档** - 已被Final_Prompts.md替代 |
| **ByteIntern_Submission.md** | 551 | 历史文档 | ⭐⭐ 实习申请材料 | **归档** - 历史性文件 |
| **SOP_v2.md** | 671 | 历史文档 | ⭐⭐ 开发过程记录 | **归档** - 42小时冲刺记录 |
| **NewsAI_workspace_v2.md** | 556 | 设计文档 | ⭐⭐ 工作区设计 | **可选保留** - 参考价值有限 |
| **Document_Implementation_Summary.md** | 206 | 技术文档 | ⭐⭐ 实现摘要 | **合并** - 并入架构文档 |

### 2.2 建议操作

#### 保留（核心文档）
- `Final_Prompts.md` → 重命名为 `AGENT_PROMPTS_MASTER.md`
- `Agent_roster_v2.md` → 重命名为 `AGENT_ROSTER.md`
- `Documents_design_v2.md` → 重命名为 `CONTENT_DESIGN.md`
- `NewsAI_project_v2.md` → 重命名为 `PROJECT_OVERVIEW.md`
- `Tables_schema_v2.md` → 重命名为 `DATABASE_SCHEMA.md`
- `KOC_persona.md` → 重命名为 `KOC_PERSONA.md`

#### 归档到 `docs/archive/`
- `AGENT_PROMPTS.md`（旧版）
- `ByteIntern_Submission.md`
- `SOP_v2.md`
- `NewsAI_workspace_v2.md`
- `Document_Implementation_Summary.md`

#### 删除
- `agentlogic.md`（不存在）
- `ClaudeCode_Execution_Prompt.md`（不存在）
- `explain_limitation.md`（已移动但可能被忽略）

---

## 三、需要更新的文档

### 3.1 README.md（最高优先级）

当前README.md内容较简单，需要全面更新为项目主入口文档。

**需要包含：**
1. 项目概述（一句话定义）
2. 核心特性（9 Agent + LangGraph + Bitable-only）
3. 快速开始（3步启动）
4. 项目结构
5. 核心流程图
6. 技术栈
7. 文档索引

### 3.2 更新docs中的核心文档

1. **PROJECT_OVERVIEW.md**（原NewsAI_project_v2.md）
   - 更新为最新架构描述
   - 添加v3.0改进点
   - 更新项目状态

2. **ARCHITECTURE.md**（新建）
   - 系统架构图
   - 数据流说明
   - Agent协作机制
   - 审改循环详解

3. **QUICKSTART.md**（更新）
   - 确保与当前代码一致
   - 添加常见问题

### 3.3 工作日志更新

更新 `worklog.md`：
- 添加0512文件夹整理记录
- 添加文档更新记录

---

## 四、下一步行动计划

1. **立即执行**：
   - [ ] 更新README.md
   - [ ] 归档旧文档
   - [ ] 重命名核心文档

2. **短期执行**：
   - [ ] 新建ARCHITECTURE.md
   - [ ] 更新PROJECT_OVERVIEW.md
   - [ ] 更新QUICKSTART.md

3. **清理**：
   - [ ] 删除/归档不再需要的文档
   - [ ] 统一文档命名规范
   - [ ] 更新worklog.md
