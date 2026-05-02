# NewsAI · Workspace

> 飞书 AI 校园挑战赛 · 多智能体虚拟组织项目仓库结构与技术栈说明

---

## 一、仓库总览

- **仓库名**：`newsai`
- **可见性**：Public（飞书赛事要求）
- **主语言**：Python 3.11
- **核心 Stack**：LangGraph + LangChain + lark-oapi + 豆包 2.0 (OpenAI 协议)
- **状态**：开发中

**一句话定位**：跑在飞书多维表格上的 AI 新闻编辑部 —— 9 个虚拟员工通过 OpenAPI 协同工作。

---

## 二、目录结构

```
newsai/
│
├── README.md                       # 项目介绍 + 一键启动指南（评委入口）
├── PROJECT.md                      # 详细项目书（产品方案）
├── WORKSPACE.md                    # 本文档（技术架构）
│
├── pyproject.toml                  # uv / pip 依赖管理
├── .env.example                    # 环境变量模板
├── .gitignore
│
├── bootstrap.py                    # ⭐ 一键复现脚本（建表+配置+跑 demo）
├── run.py                          # 主入口：启动 LangGraph 跑一轮
│
├── core/                           # ★ 共享核心层（与 trendai 仓库保持同步）
│   ├── __init__.py
│   │
│   ├── agents/                     # 9 个 Agent 定义
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseAgent 抽象类
│   │   ├── trend_scout.py          # 小哨：信息采集
│   │   ├── hook_analyst.py         # 小析：爆点分析
│   │   ├── topic_curator.py        # 小编：选题生成
│   │   ├── content_writer.py       # 小文：文字编辑
│   │   ├── visual_designer.py      # 小图：视觉设计
│   │   ├── script_writer.py        # 小播：短视频编剧
│   │   ├── reviewer.py             # 小审：审核员
│   │   ├── distributor.py          # 小发：分发策略
│   │   └── analyst.py              # 小数：数据分析师
│   │
│   ├── prompts/                    # Prompt 集中管理（按 Agent 拆分）
│   │   ├── __init__.py
│   │   ├── trend_scout.py
│   │   ├── hook_analyst.py
│   │   ├── topic_curator.py
│   │   ├── content_writer.py
│   │   ├── visual_designer.py
│   │   ├── script_writer.py
│   │   ├── reviewer.py
│   │   ├── distributor.py
│   │   ├── analyst.py
│   │   └── shared/
│   │       ├── koc_persona.py      # KOC 人设 prompt 片段
│   │       └── chinese_hooks.py    # 中文爆款基因 prompt 库
│   │
│   ├── graph/                      # LangGraph 编排
│   │   ├── __init__.py
│   │   ├── state.py                # 共享 State 定义
│   │   ├── nodes.py                # 节点函数（包装 Agent 为节点）
│   │   ├── edges.py                # 条件边逻辑（含 fan-out / fan-in）
│   │   └── builder.py              # build_graph() 工厂
│   │
│   ├── sources/                    # 信息源采集
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseSource 抽象
│   │   ├── arxiv.py                # 真爬虫
│   │   ├── hackernews.py           # 真爬虫
│   │   ├── github_trending.py      # 真爬虫
│   │   ├── reddit.py               # 真爬虫（需 PRAW key）
│   │   ├── mock_xiaohongshu.py     # mock 爆款数据
│   │   ├── mock_douyin.py          # mock 爆款数据
│   │   └── mock_x.py               # mock 爆款数据
│   │
│   ├── visual/                     # 图生成三轨
│   │   ├── __init__.py
│   │   ├── text_card.py            # 文字卡片图（HTML 渲染 + Playwright）
│   │   ├── infographic.py          # 信息图（SVG 模板）
│   │   ├── ai_image.py             # 文生图（即梦 API）
│   │   └── templates/              # HTML / SVG 模板文件
│   │       ├── card_white.html
│   │       ├── card_dark.html
│   │       ├── card_emoji.html
│   │       └── infographic_compare.svg
│   │
│   ├── llm/                        # LLM 客户端封装
│   │   ├── __init__.py
│   │   └── client.py               # 单例 ChatOpenAI（指向火山方舟）
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config.py               # 环境变量统一加载
│
├── feishu_adapter/                 # ★ 飞书专属适配层
│   ├── __init__.py
│   │
│   ├── base_client.py              # lark-oapi SDK 封装
│   ├── tools.py                    # 把 base_client 封装为 LangChain Tools
│   │
│   ├── schemas/                    # 多维表格 schema 定义
│   │   ├── __init__.py
│   │   ├── tables.py               # 10 张表的字段定义
│   │   └── views.py                # 看板视图、分组视图等配置
│   │
│   └── bootstrap/                  # 一键建表
│       ├── __init__.py
│       ├── create_app.py           # 创建多维表格 App
│       ├── create_tables.py        # 批量建表
│       └── seed_data.py            # 写入种子数据（KOC 人设、信息源配置等）
│
├── mock_data/                      # mock 数据集
│   ├── xiaohongshu_hot.json        # 小红书爆款样本（手动收集）
│   ├── douyin_hot.json
│   └── x_hot.json
│
├── tests/                          # 最小测试集
│   ├── test_lark_hello.py          # 飞书 SDK 连通性测试
│   ├── test_graph_smoke.py         # 端到端冒烟测试
│   └── test_sources.py             # 信息源采集测试
│
├── demo/                           # Demo 物料
│   ├── screenshots/                # 多维表格截图
│   ├── walkthrough.md              # 演示讲解稿
│   └── recording_script.md         # 录屏脚本
│
└── docs/                           # 进一步文档
    ├── architecture.md             # 架构详解（评委细看）
    ├── prompts_design.md           # Prompt 设计思路
    └── lark_api_notes.md           # 飞书 API 踩坑记录
```

---

## 三、核心模块说明

### 3.1 `core/` —— 业务核心（与 trendai 共享）

这一层完全不知道"飞书"或"PCG"的存在。它只负责：
- 定义 9 个 Agent 的行为
- 编排 LangGraph 状态图
- 采集信息源
- 生成图

**关键设计**：所有 Agent 通过依赖注入接收 Tool 列表 —— Tool 的具体实现由 adapter 层提供。

### 3.2 `feishu_adapter/` —— 飞书专属

把 `lark-oapi` 的 API 调用封装为：
1. **`base_client.py`**：薄封装的多维表格 CRUD（create_record, update_record, query_records, etc.）
2. **`tools.py`**：把上述 client 方法包装成 LangChain Tool，喂给 Agent

**关键设计**：Schema 定义集中在 `schemas/tables.py`，bootstrap 脚本读 schema 自动建表。**评委 clone 仓库 → 填 .env → 跑 bootstrap.py → 立刻有可用的多维表格系统**。

### 3.3 `bootstrap.py` —— 一键复现入口

```python
# 伪代码示意
def bootstrap():
    1. 读取 .env 配置
    2. 创建多维表格 App（如不存在）
    3. 批量建表（10 张业务表）
    4. 写入种子数据（KOC 人设、信息源配置）
    5. 跑一次完整 LangGraph 流程（end-to-end smoke test）
    6. 打印 Base 链接 + 每张表的访问入口
```

### 3.4 `run.py` —— 日常使用入口

```bash
python run.py --once              # 跑一轮
python run.py --watch             # 持续运行（cron 模式）
python run.py --agent topic       # 单独跑某个 Agent（调试用）
```

---

## 四、技术栈

### 4.1 核心依赖

| 库 | 版本 | 用途 | 为什么选 |
|---|---|---|---|
| `python` | 3.11 | 主语言 | LangChain 生态最佳兼容 |
| `langgraph` | latest | Agent 编排 | 状态图清晰、fan-out 友好、调试可视化 |
| `langchain` | latest | LLM 抽象 + Tools | 生态完整，避免重复造轮子 |
| `langchain-openai` | latest | LLM 客户端 | 直接用 OpenAI 协议指向火山方舟 |
| `lark-oapi` | latest | 飞书 SDK | 官方 SDK，覆盖所有 OpenAPI |
| `pydantic` | v2 | 数据模型 | LangGraph state 强校验 |
| `python-dotenv` | latest | 环境变量 | 标准做法 |
| `playwright` | latest | HTML → 图片 | 文字卡片图渲染 |
| `httpx` | latest | HTTP 客户端 | 信息源爬虫 |
| `feedparser` | latest | RSS / Atom 解析 | arXiv / GitHub Trending |
| `praw` | latest | Reddit API | 官方推荐 Python 库 |
| `loguru` | latest | 日志 | 比 logging 友好 |

### 4.2 不引入的东西（避免过度设计）

- ❌ FastAPI / Flask —— 飞书侧不需要 web 后端，直接 CLI 触发
- ❌ Redis / Celery —— 不做异步队列，LangGraph 的 fan-out 已够用
- ❌ Docker —— bootstrap.py 直接 pip install 跑，无需容器
- ❌ pytest 完整测试 —— 只写 3 个冒烟测试，黑客松不写单元测试矩阵
- ❌ Plugin 系统 / 复杂配置中心 —— 9 个 Agent hardcode，不预留扩展点

### 4.3 环境变量（`.env.example`）

```bash
# ===== LLM =====
LLM_API_KEY=your_volcengine_api_key
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=ep-2026xxxx-xxxxx     # 火山方舟 Endpoint ID

# ===== 飞书 =====
LARK_APP_ID=cli_xxxxxx
LARK_APP_SECRET=xxxxxx
LARK_BASE_APP_TOKEN=             # 首次运行 bootstrap 后填入

# ===== 即梦图像 =====
JIMENG_API_KEY=                  # 选填，留空则跳过画面图生成

# ===== Reddit =====
REDDIT_CLIENT_ID=                # 选填，留空则使用 mock
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=newsai/0.1

# ===== 运行配置 =====
KOC_PERSONA_FILE=mock_data/koc_persona.json
LOG_LEVEL=INFO
```

---

## 五、运行方式

### 5.1 评委一键复现

```bash
# 1. clone 仓库
git clone https://github.com/xxx/newsai.git
cd newsai

# 2. 安装依赖
pip install -e .
playwright install chromium

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LARK 和 LLM 的 key

# 4. 一键启动
python bootstrap.py

# 5. 查看产物
# 命令行打印 Base 链接，浏览器打开即可看到完整虚拟组织
```

### 5.2 本地开发

```bash
# 单独跑某个 Agent（调试 prompt）
python run.py --agent topic_curator

# 端到端跑一次（写入真实 Base）
python run.py --once

# 看日志
tail -f logs/newsai.log
```

---

## 六、与 TrendAI 仓库的代码同步

由于 `core/` 在两个仓库之间共享，本地开发流程：

```
本地工作目录：
~/Projects/
  ├── newsai/         <- git push 飞书赛事仓库
  ├── trendai/        <- git push PCG 赛事仓库
  └── _core_master/   <- 唯一权威 core 副本
```

**同步策略**：
- `core/` 在 `_core_master/` 里编辑（唯一真源）
- 用一个 sync 脚本：`./sync_core.sh` 把 `_core_master/core/` rsync 到两个仓库
- 写完 core 改动 → 跑 sync → 两边各自 git commit & push

**注**：由于黑客松周期短，`core/` 的改动频率高但稳定后变化不多。这种"复制式同步"比 git submodule 简单得多。

---

## 七、开发里程碑（与时间盒对齐 —— 待最终确认）

| Day | 目标 | 完成标志 |
|---|---|---|
| Day 0.5 | lark-oapi hello world + LangGraph hello world | 真实写入一条 Base 记录 + 跑通 2 节点最小图 |
| Day 1 | 端到端最小闭环（4 真源 + 全 9 Agent 串通） | bootstrap.py 跑完，Base 里有真实产出 |
| Day 2 | Prompt 调优 + 多维表格视图美化 + 录屏 | 演示效果可见，材料齐全 |
| Day 2.5 | 文档完善 + 提交 | 三件套交付 |

---

## 八、风险点与对策

| 风险 | 对策 |
|---|---|
| lark-oapi SDK 不熟悉，可能踩坑 | Day 0.5 优先做 hello world 验证 |
| 多维表格的复杂字段（关联记录、状态字段）API 不熟 | 先用最简单字段类型，复杂字段后期加 |
| 火山方舟 Doubao 2.0 在 LangChain 中的兼容性 | 已确认走 OpenAI 协议可通，先用 ChatOpenAI |
| 9 个 Agent 全跑通耗时 | 并发节点（信息源 / 爆点 / 创作）异步化 |
| Token 烧得快 | 单条 demo 限制信息源 5 条以内 |

---

## 九、附录：技术选型理由速记

**为什么 LangGraph 而非 AutoGen / CrewAI？**
- LangGraph 的状态图心智模型清晰，fan-out / fan-in 原生支持，飞书赛题要求"前一个 Agent 输出 = 后一个 context"完美匹配。
- AutoGen 偏向 A2A 对话，不是这次要的。
- CrewAI 心智过于"团队"叙事，控制粒度不如 LangGraph。

**为什么不用 OpenClaw？**
- OpenClaw 是飞书内的 Agent 运行时。我们的 Agent 跑在外部 Python 环境里，通过 OpenAPI 操作 Base，OpenClaw 这次不合适。

**为什么用 lark-oapi 而非自研 HTTP 调用？**
- lark-oapi 处理了鉴权刷新、错误码、速率限制等脏活，不重复造轮子。
- 黄梦轩老师强调 CLI，但 SDK 在工程上更稳，最终交付物的可读性也更好。
