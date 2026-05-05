# 架构版本说明

## 当前架构：v2

**v2 启用日期**：2026-05-04

## v2 与 v1 的核心差异

### Agent 阵容变化
- ❌ 删除：小析 HookAnalyst（爆点分析职能合并到小编）
- ✅ 新增：小改 Editor（独立修改专员，与小审配合做审改循环）

### 产出形态变化
- v1：所有产出塞进多维表格字段
- v2：表 + 文档双形态
  - 表（6 张）：Agent 花名册、Agent 协作日志、信源、热帖库、选题库、数据库
  - 文档（4 类）：经验文档、帖子文档、视频脚本文档、审改文档
  - KOC 人设保持表，不是文档

### 工作流变化
- v1：纯线性流水线，9 节点串行
- v2：4 Part + 1 独立
  - Part 1 信息组：小哨
  - Part 2 决策组：小编
  - Part 3 生产组（**并发**）：小文、小图、小播
  - Part 4 治理组：小审 ↔ 小改 **循环** → 小发
  - 独立复盘：小数

### 生产组一次过 + 审改在副本上
- 小文写完帖子文档 → **完成、不再改**
- 小播写完视频脚本 → **完成、不再改**
- 内容**复制副本**到审改文档 → 小审审 → 小改改 → 小审审 → ... 最多 N 次
- 审改文档累积多轮审查（一个文档不断追加 H2 标题"### 第 N 轮审查"）

## 文档版本对照

| v2 文档（即将由 claude.ai 输出） | v1 归档 |
|---|---|
| NewsAI_project_v2.md | NewsAI_project_v1_deprecated.md |
| NewsAI_workspace_v2.md | NewsAI_workspace_v1_deprecated.md |
| Tables_schema_v2.md | Tables_schema_v1_deprecated.md |
| Documents_design_v2.md | （v2 新增） |
| Agent_roster_v2.md | Agent_roster_v1_deprecated.md |

## 暂不归档但需后续更新的文档

- KOC_persona.md（v2 仍适用，第 1.4 节小析引用待 patch）
- Context.md（工作上下文）
- SOP.md（开发 SOP）

## 等待 ZQ 行动

- claude.ai 输出 v2 的 5 份新文档
- ZQ 将新文档转给 Claude Code 后开始代码改造
