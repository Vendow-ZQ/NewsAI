# NewsAI + TrendAI 开发 SOP · v2

> 版本：v2.0  
> 时间：2026-05-04 18:30 → 2026-05-07 12:00（约 42 小时冲刺）  
> 原则：**先跑通，再抛光。所有过度设计都砍。NewsAI 主战场，TrendAI 最后冲刺。**

---

## 一、总目标与时间窗

### 截止线（剩余时间）

| 项目 | 截止 | 距离 5/4 18:30 |
|---|---|---|
| **PCG（TrendAI）** | 5/6 23:59 | 约 30 小时 |
| **飞书（NewsAI）** | 5/7 12:00 | 约 42 小时 |

### 必须交付（最低标准）

| 项目 | 交付物 |
|---|---|
| **NewsAI** | 飞书 Base 7 张表（Bitable-only，4 类内容存多行文本字段）+ 9 个 Agent 串通 + 审改循环 + bootstrap.py 一键复现 + GitHub Public 仓库 + ≤3 分钟演示视频 |
| **TrendAI** | 本地 JSON 存储 + 极简 React UI + Vercel 部署 + ≤3 分钟演示视频 + PDF 项目说明文档 |

### 不做（防过度设计）

- ❌ Docker / Redis / Celery / Postgres
- ❌ 复杂前端（Next.js / shadcn / Redux）
- ❌ pytest 完整测试矩阵（只跑冒烟）
- ❌ 视频文件生成（只出脚本）
- ❌ WebSocket（用 2 秒轮询）
- ❌ \_core\_master 真源同步机制（直接复制粘贴）

---

## 二、当前状态盘点（5/4 18:30）

### ✅ 已完成

| 阶段 | 内容 |
|---|---|
| Stage 1.1 | 飞书 lark-oapi SDK hello world |
| Stage 1.2 | 豆包 LLM hello world |
| Stage 1.3 | LangGraph hello world |
| Stage 1.4 扩展 | 飞书 Bitable 完整功能（建表、字段 CRUD、视图、批量）|
| Stage 1.5 | v1 → v2 文档归档（4 份 _deprecated + VERSION.md） |
| Stage 1.6 | v2 5 份核心文档全部沉淀 |

### 🔄 进行中

| 阶段 | 内容 | 责任 |
|---|---|---|
| 字段类型映射验证 | test_field_types_smoke.py（含多行文本大字段测试） | Claude Code |
| analytics_mock.json | mock 数据准备 | Claude Code |
| Bitable-only 架构确认 | 更新 4 份文档，删除 DocStorage 相关代码 | Claude Code |

### ⏸ 阻塞中（待 v2 文档转给 Claude Code）

| 阶段 | 内容 |
|---|---|
| 代码改造（v1 骨架 → v2 实现） | 9 个 Agent + Storage + Graph |
| bootstrap.py v2 重写 | 7 张表 + 4 类文档夹 + 种子数据 |

---

## 三、Stage 划分（v2 完整版）

### Stage 2 · Bitable 字段验证（5/4 晚 19:00-20:00）🔧 关键路径

**目标**：验证 Bitable 多行文本字段能否承载 4 类内容产物，确认大字段写入性能。

**任务**：
1. 写 `test_field_types_smoke.py`：8 种字段类型全覆盖测试，重点测试多行文本
2. 写 `test_large_text_field.py`：模拟 9000 字（3 万字）内容写入多行文本字段
3. 准备 `analytics_mock.json`：6 条 mock 数据（高/中/低各 2 条）

**验收**：
- ✅ 所有字段类型 CRUD 正常
- ✅ 多行文本字段可写入 100,000 字符（约 3 万字）无截断
- ✅ 读取速度 < 500ms（单条记录）
- ✅ analytics_mock.json 能被 LocalStorage 加载

**关键决策**：
- **确认 Bitable-only 架构**：多行文本字段足够存储 4 类内容产物，无需飞书云文档

**并行性**：3 个任务**完全并行**，不依赖。

---

### Stage 3 · Storage 接口实现（5/4 晚 20:00-22:00）🏗️ 串行底座

**目标**：v2 的 Storage 抽象层落地（Bitable-only，无文档接口）。

**任务**：
1. **核心抽象层**：
   - `core/storage/interface.py` —— `BaseStorage` 抽象基类（4 方法）
   - `core/storage/id_generator.py` —— 业务 ID 生成器（`{表前缀}-{YYYYMMDD}-{NNN}`）

2. **飞书 Base 实现**：
   - `feishu_adapter/base/feishu_storage.py` —— 实现 `BaseStorage`
   - `feishu_adapter/base/id_mapping.py` —— 业务 ID ↔ 飞书 record_id 映射
   - `feishu_adapter/base/tables.py` —— 7 张表 schema（按 Tables_schema_v2_bitable.md）
   - **注意**：4 类内容产物直接写多行文本字段，不创建飞书文档

3. **测试**：
   - `test_storage_interface.py` —— Storage 接口冒烟（仅 Base）
   - `test_topic_content_write.py` —— 模拟小文写入帖子内容字段

**验收**：
- ✅ 通过接口创建一条 TOPIC 记录、查询、更新、删除
- ✅ 通过接口写入多行文本字段（模拟 4 平台版本内容）
- ✅ 读取多行文本字段，内容完整无截断

**并行性**：1、2 两个任务**可串行**（有依赖）；测试在最后跑。

**注意**：`tables.py` 写完后**必须严格按 Tables_schema_v2_bitable.md** —— 字段名、类型、必填性都对照检查，特别是 4 个多行文本内容字段。

---

### Stage 4 · BaseAgent 模板 + 小哨端到端（5/5 上午 8:00-12:00）🎯 关键里程碑

**目标**：用模板方法把第 1 个 Agent（小哨）端到端跑通，验证整套架构。

**任务**：
1. 升级 `core/agents/base.py`：v2 模板方法（参考 Agent_roster_v2.md）
2. 实现装饰器 `core/decorators/log_work.py`：自动写工作日志
3. 实现 `core/agents/trend_scout.py`（小哨）：
   - 读 SRC 表（信源配置）
   - 调 4 真源 + 3 mock 源（按 SRC.是否启用）
   - LLM 打热度评分 + 主题标签
   - 写 TREND 表
4. 实现 `core/sources/`（已存在骨架）：填实 7 个源的爬虫逻辑
5. 测试：`test_trend_scout_e2e.py`

**验收**：
- ✅ 跑通 `test_trend_scout_e2e.py`
- ✅ 飞书 TREND 表里有 ≥10 条真实热帖（含真源）
- ✅ Agent协作日志表里有 1 条小哨的字节风格日报
- ✅ Mock 数据也能跑通（mock 3 源各 5 条）

**为什么先做小哨**：
- 小哨没有上游依赖，最容易跑通
- 跑通它就验证了：BaseAgent 模板 + Storage 接口 + 装饰器 + 信源系统
- 跑通后剩下 8 个 Agent 是**流水线作业**

**并行性**：必须串行，这是关键路径。

---

### Stage 5 · 8 个 Agent 流水线铺开（5/5 下午 14:00-19:00）🚀 平推

**目标**：复用 BaseAgent 模板，把剩余 8 个 Agent 全部填实。

**Agent 实现优先级**（按业务流程排）：

| 优先级 | Agent | 文件 | 上游 | 下游 |
|---|---|---|---|---|
| 1 | 小编 | topic_curator.py | 小哨 | 生产组 3 人 |
| 2 | 小文 | content_writer.py | 小编 | 小审 |
| 3 | 小图 | visual_designer.py | 小编 | 小审 |
| 4 | 小播 | script_writer.py | 小编 | 小审 |
| 5 | 小审 | reviewer.py | 生产组 | 小改 / 小发 |
| 6 | **小改 ⭐** | editor.py（v2 新增） | 小审 | 小审 |
| 7 | 小发 | distributor.py | 小审 | 小数 |
| 8 | 小数 | analyst.py | 小发 | 反馈小编 |

**每个 Agent 的开发模板**：
1. 复制 BaseAgent 子类骨架
2. 填 4 个 hook 方法：`_read_upstream` / `_invoke_tools` / `_invoke_llm` / `_write_storage`
3. 写 prompt（参考 KOC_persona 的字段映射）
4. 单 Agent 冒烟测试

**Prompt 来源**：
- 每个 Agent 的角色定义 → `Agent_roster_v2.md`
- 中文爆款基因 → `core/prompts/shared/chinese_hooks.py`
- KOC 人设引用 → `core/prompts/shared/koc_persona.py`

**并行性**：
- **可并行**：小文 / 小图 / 小播（生产组三人对等）
- **必须串行**：小编 → 生产组、小审 → 小改、小审 → 小发、小发 → 小数

**验收**（每个 Agent 单独）：
- ✅ 单 Agent 冒烟测试通过
- ✅ 该 Agent 的产出能被下游正确读取
- ✅ Agent协作日志有对应的字节日报

---

### Stage 6 · LangGraph 编排 + 审改循环（5/5 晚 19:00-23:00）🔁 核心难点

**目标**：把 9 个 Agent 串成完整状态图，含审改循环。

**任务**：
1. 升级 `core/graph/state.py`：v2 State 字段（含 revision_count, review_verdict）
2. 升级 `core/graph/builder.py`：
   - Linear: 小哨 → 小编
   - Fan-out: 小编 → 生产组 3 人并发
   - Fan-in: 生产组 → 小审
   - **Cyclic**: 小审 ↔ 小改（max=3）
   - Linear: 小审通过 → 小发 → 小数
3. 升级 `core/graph/edges.py`：审改循环的条件边
4. 测试：`test_full_pipeline_smoke.py`

**审改循环关键代码**（决定整个 v2 成败）：
```python
g.add_conditional_edges(
    "reviewer",
    lambda state: 
        "editor" if (state.review_verdict == "needs_revision" 
                     and state.revision_count < 3)
        else "distributor",
)
g.add_edge("editor", "reviewer")  # 改完回到审
```

**验收**：
- ✅ `python run.py --once` 端到端跑通
- ✅ 至少 1 条选题经历完整 9 节点
- ✅ 至少 1 条选题触发审改循环（人工设计一条会被打回的稿子）
- ✅ 飞书 Base 看到 TOPIC 状态完整流转
- ✅ 审改文档累积 2-3 个章节

**并行性**：必须串行。

---

### Stage 7 · bootstrap.py + 视图美化（5/6 上午 8:00-12:00）✨ 演示打磨

**目标**：让评委 5 分钟一键复现 + 飞书界面美观。

**任务**：
1. **bootstrap.py 完整版**：
   - 创建飞书 Base 应用
   - 建 7 张表（按 schema）+ 字段 + 看板视图
   - 创建 `NewsAI产物/` 文件夹及 4 子文件夹
   - 写入种子数据（KOC 人设 + 9 员工 + 7 信源）
   - 跑一次完整流程（端到端冒烟）
   - 打印链接（Base + 文档库）
   - 配置评委权限（如果 .env 有 JUDGE_USER_IDS）

2. **飞书 Base 视图美化**：
   - 选题库：按状态分列的看板视图
   - Agent 花名册：按部门分组的卡片视图
   - Agent 协作日志：按花名筛选的分组视图
   - 数据库：按综合评分排序的表格视图

3. **README.md 完整版**：评委读这一份就够

**验收**：
- ✅ 一台干净环境，git clone + .env 配置 + python bootstrap.py，5 分钟内复现完整 demo
- ✅ 飞书 Base 看板视图视觉冲击强
- ✅ README 包含一键复现指南 + 评委体验路径

**并行性**：1、2、3 可并行。

---

### Stage 8 · TrendAI 冲刺（5/6 下午 14:00-22:00）⚡ 最后一搏

**目标**：完成 PCG 截止前提交（5/6 23:59）。

**任务**：
1. **代码迁移**（约 30 分钟）：
   - 复制 NewsAI/core/ → TrendAI/core/
   - 删 NewsAI 专属导入
   
2. **本地 Storage 实现**（约 1 小时）：
   - `pcg_adapter/local_storage.py` —— 实现 `BaseStorage`（JSON 文件）
   - `pcg_adapter/local_doc_storage.py` —— 实现 `DocStorage`（本地 markdown 文件）

3. **极简 React UI**（约 2 小时）：
   - `frontend/src/pages/Home.tsx`：1 个大按钮 + 3 个区块
   - `frontend/src/pages/Workspace.tsx`：7 阶段流水线（可选）
   - `frontend/src/api/client.ts`：调后端 API

4. **FastAPI 后端**（约 1 小时）：
   - `pcg_adapter/api/main.py`：`/workflow/start` + `/stages/{stage}` + `/persona`

5. **Vercel + Render 部署**（约 1 小时）：
   - 前端 Vercel
   - 后端 Render 或 Railway
   - 配置环境变量

6. **录屏 + PDF 文档 + 提交**（约 2.5 小时）：
   - 录屏：≤3 分钟，含语音讲解
   - PDF：参考 PCG 提交规范 8 部分结构
   - 文件命名：`ZQ_技术公线赛道_TrendAI_*.{mp4,pdf}`
   - GitHub Public 仓库
   - 在线提交表单填写

**砍需求预案**（如时间不够）：
1. 砍 Workspace 页面，只保留 Home
2. 砍小数 Agent
3. 砍 Vercel 部署，本地 demo 用 localtunnel 临时暴露
4. 砍审改循环（直接小审通过）

**底线**：必须有 Demo 链接 + 录屏 + PDF。

---

### Stage 9 · NewsAI 终交付（5/7 上午 8:00-12:00）🏁 收官

**目标**：5/7 12:00 前完成飞书赛事最终提交。

**任务**：
1. **最终验证**（约 1 小时）：
   - 干净环境 git clone + bootstrap.py 验证
   - 飞书 Base 数据完整性检查
   - 飞书文档 4 类产出检查
   
2. **录屏**（约 1.5 小时）：
   - ≤3 分钟，含语音讲解
   - 演示路径：bootstrap → Base 看板 → 文档库 → 审改循环 → 数据回流
   
3. **PDF 文档**（约 1 小时）：
   - 项目说明文档（基于 NewsAI_project_v2.md）
   
4. **个人阶段成果小结**（约 30 分钟）：
   - 三日一份的飞书要求
   - 至少补 1 份覆盖 5/4-5/6 进展
   
5. **提交**（约 30 分钟）：
   - GitHub Public 仓库 final push
   - 飞书赛事在线提交表单

**验收**：
- ✅ 5/7 12:00 前所有材料提交
- ✅ 评委账号能访问飞书 Base 和文档库

**并行性**：录屏、PDF、个人小结可并行准备。

---

## 四、SOP 时间轴一图流

```
5/4 18:30 现在
  │
  ├─ 19:00-21:00  Stage 2 飞书文档 SDK 验证（3 任务并行）
  ├─ 21:00-23:00  Stage 3 Storage 双接口实现
  │
5/5 (周一)
  ├─ 08:00-12:00  Stage 4 BaseAgent + 小哨端到端 ⭐
  ├─ 14:00-19:00  Stage 5 8 Agent 流水线铺开
  ├─ 19:00-23:00  Stage 6 Graph 编排 + 审改循环 ⭐
  │
5/6 (周二)
  ├─ 08:00-12:00  Stage 7 bootstrap + 视图美化
  ├─ 14:00-22:00  Stage 8 TrendAI 冲刺
  ├─ 23:59        🚨 PCG 截止
  │
5/7 (周三)
  ├─ 08:00-12:00  Stage 9 NewsAI 终交付
  ├─ 12:00        🚨 飞书截止
```

---

## 五、并行 vs 串行总览

### ✅ 可并行（多线程开发）

- Stage 2 内部 3 个任务（文档/字段/mock 数据）
- Stage 3 内部 1+2+3（接口 / Base 实现 / Docs 实现）
- Stage 5 中的小文 / 小图 / 小播（生产组对等）
- Stage 7 内部 bootstrap / 视图 / README
- Stage 9 录屏 / PDF / 个人小结

### 🔧 必须串行（关键路径）

- Stage 2 → Stage 3（文档 SDK 决策影响 DocStorage 实现）
- Stage 3 → Stage 4（Storage 是 Agent 的依赖）
- Stage 4 → Stage 5（小哨跑通才能验证模板）
- Stage 5 → Stage 6（Agent 跑通才能编排）
- Stage 6 → Stage 7（Graph 跑通才能 bootstrap）
- Stage 7 → Stage 8（NewsAI 稳定才能复制到 TrendAI）

---

## 六、紧急砍需求预案（按顺序）

| 优先级 | 砍什么 | 影响 |
|---|---|---|
| 1 | TrendAI 的 Workspace 页面 | 只保留 Home |
| 2 | 小数 Agent（数据复盘）| 跑流程不需要它 |
| 3 | 小播 Agent（视频脚本）| 只跑图文 |
| 4 | 飞书 Base 视图美化 | 数据完整即可 |
| 5 | TrendAI Vercel 部署 | localtunnel 临时暴露 |
| 6 | 审改循环（max_revisions=1）| 小审一次过 |
| 7 | 真爬虫源（只跑 mock）| 演示效果不变 |

**底线（绝对不能砍）**：
- 小哨 → 小编 → 小文 → 小审 → 小发 主线必须通
- bootstrap.py 必须能跑
- 飞书 Base + 至少 1 类文档必须能产出
- TrendAI 必须有 Demo 链接（即使不部署）

---

## 七、每日站会问 ZQ

每天 22:00 Claude Code 自问自答 + 上报 ZQ：

1. **今天完成了哪些 Stage？**（看产出，不看工时）
2. **明天的关键路径阻塞点是什么？**
3. **有什么需要 ZQ 决定或提供的资源？**（Reddit key？爆款样例？API 额度？）

---

## 八、Git 策略

### 分支模型（极简）

```
main 分支：始终可运行
    │
    ├── stage2/doc-validation
    ├── stage3/storage-impl
    ├── stage4/trend-scout-e2e
    ├── stage5/agents-rollout
    ├── stage6/graph-cyclic
    ├── stage7/bootstrap
    ├── stage8/trendai
    └── stage9/final
```

### Push 节奏

- 每 Stage 完成立即 push 该 Stage 分支
- 每 Stage 通过 ZQ 验收后 merge 到 main
- 每天 22:00 push worklog.md

### Commit 消息

```
[Stage X] 模块: 做了什么

例：
[Stage 4] agents: 小哨端到端跑通
[Stage 6] graph: 审改循环 max_revisions=3
```

---

*SOP v2 沉淀完成于 2026-05-04 18:30 SGT*  
*基于 v1.1 升级，反映 v2 架构（删小析、加小改、表+文档双形态、审改循环）*

---

## 九、Stage 10 - Bug修复与验证（5/4 晚 22:00-24:00）🔧

**目标**: 修复端到端测试发现的P0/P1 bug，完成全流程验证。

### Bug修复清单

#### 🔴 P0 - 阻塞性Bug（今晚必须修复）

| # | Bug | 位置 | 修复方案 | 负责 |
|---|-----|------|---------|------|
| 1 | LangGraph并发状态错误 | `core/graph/nodes.py` | 移除并发节点对state的修改，或改用Annotated类型 | Claude |
| 2 | Agent协作日志字段名错误 | 所有Agent的 `_log_work` | 核对LOG表schema，修正字段名 | Claude |
| 3 | 爬虫字符串Slice错误 | `core/sources/arxiv.py`, `github_trending.py` | 强制转换limit为int | Claude |

#### 🟡 P1 - 重要Bug（今晚修复）

| # | Bug | 位置 | 修复方案 | 负责 |
|---|-----|------|---------|------|
| 4 | 日期时间格式转换错误 | Agent写入方法 | 使用 `feishu_base.py` 的日期转换工具 | Claude |
| 5 | HackerNews类型比较错误 | `core/sources/hackernews.py` | 强制转换score为int | Claude |
| 6 | Mock源slice错误 | `core/sources/mock_*.py` | 同Bug #3 一并修复 | Claude |

#### 🟢 P2 - 次要Bug（明日可选）

| # | Bug | 位置 | 修复方案 | 负责 |
|---|-----|------|---------|------|
| 7 | 编码问题（日志乱码） | `run.py` | 设置stdout编码为utf-8 | 可选 |
| 8 | Reddit API未配置 | - | graceful degradation，无需修复 | - |

### 验证测试流程

每修复一个P0 bug，立即运行：

```bash
python run.py --once
```

验证通过标准：
- [ ] 小哨能抓取并写入热帖（≥5条）
- [ ] 小编能创建选题（≥1条）
- [ ] 生产组3人完成内容生成
- [ ] 审改循环正常（最多3轮）
- [ ] 小发完成分发计划
- [ ] 全流程无报错

### 修复后Commit

```bash
git add -A
git commit -m "[Stage 10] fix: 修复端到端测试发现的P0/P1 bug

- 修复LangGraph并发状态错误
- 修复Agent协作日志字段名
- 修复爬虫slice错误
- 修复日期时间格式转换
- 验证全流程通过

Co-Authored-By: Claude"
```

---

## 十、当前项目状态（2026-05-04 23:00）

### ✅ 已完成（Completed）

| Stage | 内容 | 产出 | 验证方式 |
|-------|------|------|----------|
| Stage 1 | Hello World三件套 | 飞书/LLM/LangGraph连通 | 5个测试脚本通过 |
| Stage 2 | Bitable字段验证 | 多行文本字段测试通过 | test_field_types_smoke.py |
| Stage 3 | Storage接口实现 | 7张表CRUD + IDMapping | test_storage_interface.py |
| Stage 4 | BaseAgent + 小哨 | 端到端跑通 | test_trend_scout_e2e.py |
| Stage 5 | 8个Agent铺开 | 9个Agent全部实现 | 代码审查完成 |
| Stage 6 | LangGraph编排 | Graph构建完成 | test_graph_smoke.py |
| Stage 7 | Bootstrap | 27条种子数据 | bootstrap.py 运行成功 |
| Stage 9 | 第一次端到端测试 | 完成，发现8个bug | run.py --once |

### 🔄 进行中（In Progress）

| Stage | 内容 | 状态 | 预计完成 |
|-------|------|------|----------|
| Stage 10 | Bug修复与验证 | ✅ 已完成 | 5/6 22:00 |
| Stage 11 | 飞书Base视图美化 | 🟡 进行中 | 5/6 24:00 |

### ⏳ 待启动（Pending）

| Stage | 内容 | 计划时间 | 优先级 |
|-------|------|----------|--------|
| Stage 12 | README完善 | 5/6 24:00-02:00 | P1 |
| Stage 13 | 演示视频录制 | 5/6 08:00-10:00 | P0 |
| Stage 14 | TrendAI最后冲刺 | 5/6 10:00-22:00 | P0 |
| Stage 15 | 最终提交 | 5/7 08:00-12:00 | P0 |

### 📊 代码与测试统计

**代码统计**：
```
语言         文件数    代码行数
Python       42        ~3,800
Markdown     15        ~2,500
JSON         8         ~1,200
总计         65        ~7,500
```

**测试状态汇总**：

| 测试文件 | 目的 | 状态 | 备注 |
|----------|------|------|------|
| test_lark_hello.py | 飞书SDK连通性 | ✅ 通过 | Stage 1.1 |
| test_lark_complete.py | 飞书完整功能 | ✅ 通过 | Stage 1.1扩展 |
| test_doubao_hello.py | LLM连通性 | ✅ 通过 | Stage 1.2 |
| test_graph_hello.py | LangGraph连通性 | ✅ 通过 | Stage 1.3 |
| test_bitable_full.py | Bitable完整功能 | ✅ 通过 | Stage 2 |
| test_storage_interface.py | Storage接口 | ✅ 通过 | Stage 3 |
| test_trend_scout_e2e.py | 小哨端到端 | ✅ 通过 | Stage 4 |
| test_graph_smoke.py | Graph构建 | ✅ 通过 | Stage 6 |
| test_sources.py | 信源采集 | ⚠️ 部分通过 | Mock源通过，真源有bug |

**测试覆盖率**：
- ✅ 已测试：飞书SDK、LLM、LangGraph、Storage、BaseAgent、小哨Agent
- ⚠️ 部分测试：信源采集（Mock数据通过，真实爬虫有类型错误）
- ❌ 未测试：完整9-Agent流水线（被P0 Bug阻塞）

### 🐛 Bug清单与修复状态

#### 🔴 P0 - 阻塞性Bug（今晚必须修复）✅ 已完成

| # | Bug | 位置 | 影响 | 修复方案 | 状态 |
|---|-----|------|------|----------|------|
| 1 | LangGraph并发状态错误 | `core/graph/nodes.py` | 生产组无法并行 | state.error改为Annotated errors列表 | ✅ 已修复 |
| 2 | Agent协作日志字段名错误 | 所有Agent的 `_log_work` | 日志无法写入 | 核对LOG表schema，修正字段名 | ✅ 已修复 |
| 3 | 爬虫字符串Slice错误 | `arxiv.py`, `github_trending.py` | 小哨无法获取真源数据 | 强制转换limit为int | ✅ 已修复 |

#### 🟡 P1 - 重要Bug（今晚修复）✅ 已完成

| # | Bug | 位置 | 影响 | 修复方案 | 状态 |
|---|-----|------|------|----------|------|
| 4 | 日期时间格式转换错误 | Agent写入方法 | 记录时间字段失败 | 添加convert_datetime_to_timestamp工具 | ✅ 已修复 |
| 5 | HackerNews类型比较错误 | `hackernews.py` | HN源无法过滤 | 强制转换limit为int | ✅ 已修复 |
| 6 | Mock源slice错误 | `mock_*.py` | Mock数据获取失败 | 已有int转换，无需修复 | ✅ 已验证 |

#### 🟢 P2 - 次要Bug（明日可选）

| # | Bug | 位置 | 影响 | 处理方案 | 状态 |
|---|-----|------|------|----------|------|
| 7 | 编码问题（日志乱码） | `run.py` | 中文显示为� | 设置stdout编码为utf-8 | ⏳ 可选 |
| 8 | Reddit API未配置 | - | 警告但不影响流程 | graceful degradation | ✅ 无需修复 |

### 🎯 当前阻塞点与解决路径

**主要阻塞点**：
1. **LangGraph并发状态错误** - 阻止生产组并行执行
2. **字段名不匹配** - 阻止Agent日志写入
3. **爬虫数据错误** - 阻止小哨获取真实数据

**解决路径**：
```
Step 1: 修复Bug #3, #5, #6（爬虫slice错误）→ 小哨可获取真实数据
Step 2: 修复Bug #2（日志字段名）→ Agent日志可正常写入
Step 3: 修复Bug #1（并发状态）→ 生产组可并行执行
Step 4: 修复Bug #4（日期格式）→ 所有记录时间字段正常
Step 5: 运行 `python run.py --once` 验证全流程
```

**解决后预计**: 30分钟内可跑通全流程。

### ✅ Stage 10 验收标准（已完成）

- [x] P0 Bug全部修复
- [x] P1 Bug全部修复
- [x] `python run.py --once` 完整跑通无报错
- [x] 小哨能抓取并写入≥5条热帖（含真源）
- [x] 小编能创建≥1条选题
- [x] 生产组3人完成内容生成
- [x] 审改循环正常（最多3轮）
- [x] 小发完成分发计划

**实际完成时间**: 2026-05-06 20:00  
**验证结果**: 9个Agent完整跑通，数据正确写入7张表，审改循环正常退出

---

*SOP v2 更新于 2026-05-04 23:00 SGT*  
*更新内容: 补充测试状态汇总、Bug修复状态跟踪、Stage 10验收标准*


---

## Stage 11 · Prompt工程v2.0落地（5/7 02:00-03:00）✅ 完成

**目标**: 基于 Final_Prompts.md v2.0 工程级重写，更新所有 Agent 的 System Prompt。

**设计原则**（来自 Anthropic/MicroSoft 最佳实践）：
1. XML结构化分区 - role/context/rules/examples/self_check 标签
2. Few-Shot示例 - 每个Agent 3+示例（正例+反例+边界例）
3. 人设翻译 - 抽象KOC人设→可执行标准
4. Thinking块 - 强制CoT思考，提升推理准确率40%+
5. 输出契约 - 严格JSON schema + 字数上限
6. 单一职责 - 每个Agent只做一件事
7. 自检清单 - 输出前LLM自我review

**更新清单**:

| Agent | 文件 | 核心改进 |
|-------|------|----------|
| 小哨 | trend_scout.py | XML结构化+评分维度 |
| 小编 | topic_curator.py | 3关筛查+5维度爆点 |
| 小文 | content_writer.py | 4平台铁律+中文爆款 |
| 小图 | visual_designer.py | 3类图决策树 |
| 小播 | script_writer.py | 抖音/B站脚本铁律 |
| 小审 | reviewer.py | 4维度审查+问题清单 |
| 小改 | editor.py | 精确修改+changelog |
| 小发 | distributor.py | 黄金时段+错峰策略 |
| 小数 | analyst.py | 数据回流+月度沉淀 |

**验收标准**:
- [x] 9个Agent全部更新System Prompt
- [x] worklog.md, README.md, SOP_v2.md 已更新

---

*SOP v2 更新于 2026-05-07 02:30 SGT*
