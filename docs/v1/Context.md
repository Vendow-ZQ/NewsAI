# Competition · 工作上下文

> 更新时间：2026-05-03  
> 状态：P0/P1 已完成，等 ZQ 批改 Tables_schema.md 后启动 P2

---

## 一、工作原则（不可违背）

### 1. 动手前必须确认
- **"你不要轻易动手"** —— 哪怕看起来讨论完毕，**必须再问一句"可以开始了吗"**
- **追问 → 对齐 → 拍板 → 执行**，拒绝边写边改
- 关键判断（表结构、KOC 人设、架构变更）**ZQ 亲自拍板**，我提供选项+推荐，不替决定

### 2. 代码真实可用
- **"能跑通，因为我自己也很想用这套东西"** —— 代码要真能跑，不是 demo 应付
- mock 范围诚实标注，真爬虫/假数据必须清晰区分
- 架构要工业级（评委认得出来），但**不过度设计**

### 3. 极简执行
- **不要冗杂系统**—— 用不到的模块、预设的扩展点、"为了灵活而灵活"的抽象，全部砍掉
- 先跑通端到端最小闭环，再回头加肉
- 两个 hello world 验证前（lark-oapi SDK + LangGraph），不写任何架构代码

### 4. 代码同步策略
- `_core_master/` 是唯一真源
- `sync_core.sh` 复制到两个仓库，不用 git submodule
- 各仓库各自 git push

---

## 二、项目概况

| 项目 | 赛事 | 截止 | 优先级 | Agent 数 |
|---|---|---|---|---|
| **NewsAI** | 飞书 AI 校园挑战赛 | 5月7日 12:00 | 主战场 | 9（含小播） |
| **TrendAI** | 腾讯 PCG 赛题5 | 5月6日 23:59 | 副战场 | 9（含小播，演示时极简模式不跑） |

**核心策略**：同一套 LangGraph core，两个 adapter（feishu / local），交付到两独立仓库。

---

## 三、已敲定（不再讨论）

### 技术栈
- **编排**：LangGraph StateGraph，粗粒度并发（3处：信息源/爆点/创作）
- **LLM**：`langchain-openai.ChatOpenAI` → 火山方舟 Doubao 2.0
- **飞书**：`lark-oapi` SDK，**不用 CLI**
- **图生成**：HTML 文字卡片 + SVG 信息图 + 即梦 API（画面图）
- **前端（仅 TrendAI）**：React 18 + Vite + TS + Tailwind，不用 Next.js/shadcn/Redux
- **后端（仅 TrendAI）**：FastAPI + 本地 JSON（默认）/ SQLite（可选）

### 信息源
- **4 真爬虫**：arXiv API / HackerNews / GitHub Trending / Reddit（需 ZQ 确认是否申请 key）
- **3 mock**：小红书 / 抖音 / X（热帖样本，待确认数据来源）

### 架构决策
- **Storage 抽象层**：`core/storage/interface.py` 定义统一接口，`FeishuStorage` / `LocalStorage` 分别实现
- 飞书 Base 当业务系统（非数据库），**11 张表**（新增 Agent协作日志）
- KOC 人设表是"宪法"，Agent 花名册是"虚拟组织架构"，Agent 协作日志是"工作日报"
- 视频脚本 Agent（小播）：两边都是 9 个 Agent，TrendAI 演示时极简模式不跑视频脚本
- **无**：Docker/Redis/Celery/Postgres/Auth/Plugin/复杂配置中心

---

## 四、已完成（P0/P1）

| 阶段 | 交付物 | 状态 |
|---|---|---|
| **P0** | Storage 抽象层：`core/storage/interface.py` | ✅ 已完成 |
| **P0** | `FeishuStorage` 实现（lark-oapi SDK） | ✅ 已完成 |
| **P0** | `LocalStorage` 实现（JSON 文件） | ✅ 已完成 |
| **P0** | TrendAI 补齐 `script_writer.py`（9 个 Agent） | ✅ 已完成 |
| **P1** | **11 张表 Schema 提案** | ✅ 已输出到 `Tables_schema.md` |

## 五、待 ZQ 拍板（P2-P6）

| 优先级 | 事项 | 当前状态 |
|---|---|---|
| **P2** | **Tables_schema.md 批改** | 等你确认/调整 8 张表字段 |
| **P3** | **时间盒（Day 0.5/1/2）** | 给了建议方案，你说"再议，最后聊" |
| **P4** | **Reddit Developer Key** | 是否花 30 分钟申请 PRAW？ |
| **P5** | **Mock 爆款数据来源** | 你手抄 5-10 条真实 vs 我硬编？ |
| **P6** | **TrendAI 实时推送** | WebSocket vs 2秒轮询（我倾向轮询） |

**P2 是当前阻塞项**，等你批改 Tables_schema.md 后才能写表的代码。

---

## 五、最终交付物

### NewsAI（5月7日）
- [ ] GitHub 公开仓库 + 完整代码
- [ ] `bootstrap.py`：一键建表+配置+冒烟测试+打印 Base 链接
- [ ] **11 张 Base 表 schema** + 种子数据（KOC 人设、9 名员工、信息源配置）
- [ ] 9 个 Agent 全串通，端到端可跑
- [ ] 演示视频 ≤3 分钟

### TrendAI（5月6日，更早）
- [ ] GitHub 公开仓库 + 完整代码
- [ ] Vercel 部署链接（前端）+ Render/Railway（后端）
- [ ] 极简模式 UI（1 按钮 + 3 区块）
- [ ] 工作台模式 UI（7 阶段导航 + Agent 日志）
- [ ] 演示视频 ≤3 分钟

---

## 六、下一步（等待指示）

**当前阻塞**：等 ZQ 批改 `Tables_schema.md` 中的 8 张表 schema。

建议启动顺序：
1. 你批改 Tables_schema.md（重点看末尾 10 个待拍板问题）
2. 我按批改后的 schema 写代码（或你先确认"按这个来"）
3. 跑 Hello World 1（lark-oapi 建表写记录）
4. 跑 Hello World 2（LangGraph 2 节点最小图）
5. 端到端最小闭环（4 真源 → 1 个 Agent → 写 Base）
6. 铺开 9 个 Agent + 前端

---

## 七、文档权威分层（内化）

| 等级 | 文档 | 作用 |
|---|---|---|
| **L1 真理来源** | `KOC_persona.md`, `Agent_roster.md` | 数据 schema 唯一真源 |
| **L2 项目定位** | `NewsAI_project.md`, `TrendAI_project.md`, etc. | 产品逻辑，大部分有效 |
| **L3 历史沉淀** | `HANDOFF.md` | 早期文档，与 L1/L2 冲突时作废 |
| **L4 工作流程** | `Context.md`, `worklog.md` | 协作规则，机械层 |

---

## 八、关键引用（保留原话）

> "你不要轻易动手。你问完所有东西也要问我一句才能开始干活！！"

> "能跑通，因为我自己也很想用这套东西 u know?"

> "界面是极简的，默认全自动，不是把所有东西都放到明面上炫耀。"

> "P10：屌就完事了。"

---

**状态**：等待 ZQ 说"开干"，或继续对齐 P1-P5。