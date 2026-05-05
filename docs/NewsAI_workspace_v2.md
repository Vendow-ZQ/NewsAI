# NewsAI · Workspace · v2

> v2 架构的仓库结构、技术栈、运行方式说明。

---

## v2 关键升级（vs v1）

| 维度 | v1 | v2 |
|---|---|---|
| **adapter 层** | 仅 feishu_adapter（多维表格）| feishu_adapter（**Base + Docs 双栈**）|
| **Storage 抽象** | 仅 BaseStorage | **BaseStorage + DocStorage** |
| **Agent 文件** | 9 个（含 hook_analyst）| 9 个（删 hook_analyst，加 editor）|
| **graph builder** | 线性 | **含 fan-out + 循环** |
| **新增模块** | — | `markdown_to_lark_blocks` 转换器 |
| **归档目录** | — | `_archived/`（v1 残留） |

---

## 一、仓库总览

- **仓库名**：`NewsAI`
- **可见性**：Public（飞书赛事要求）
- **主语言**：Python 3.11
- **核心 Stack**：LangGraph + LangChain + lark-oapi + 豆包（OpenAI 协议）+ 即梦
- **状态**：v2 改造中

**一句话定位**：跑在飞书 Base + 飞书文档生态上的 AI 新闻编辑部。

---

## 二、目录结构（v2）

```
NewsAI/
│
├── README.md                       # 项目介绍 + 一键启动
├── PROJECT.md                      # 软链 → docs/NewsAI_project_v2.md
├── WORKSPACE.md                    # 软链 → docs/NewsAI_workspace_v2.md
│
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── bootstrap.py                    # ⭐ 一键复现脚本
├── run.py                          # 主入口
│
├── core/                           # ★ 业务核心层
│   ├── __init__.py
│   │
│   ├── agents/                     # 9 个 Agent (v2)
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseAgent 抽象类（v2 升级模板方法）
│   │   ├── trend_scout.py          # EMP-001 小哨
│   │   ├── topic_curator.py        # EMP-002 小编（吸收原小析职能）
│   │   ├── content_writer.py       # EMP-003 小文
│   │   ├── visual_designer.py      # EMP-004 小图
│   │   ├── script_writer.py        # EMP-005 小播
│   │   ├── reviewer.py             # EMP-006 小审（v2 改为审改循环模式）
│   │   ├── editor.py               # ⭐ EMP-007 小改（v2 新增）
│   │   ├── distributor.py          # EMP-008 小发
│   │   ├── analyst.py              # EMP-009 小数
│   │   │
│   │   └── _archived/              # v1 归档
│   │       └── hook_analyst_v1.py  # 小析（已合并到小编）
│   │
│   ├── prompts/                    # Prompt 集中管理
│   │   ├── __init__.py
│   │   ├── trend_scout.py
│   │   ├── topic_curator.py
│   │   ├── content_writer.py
│   │   ├── visual_designer.py
│   │   ├── script_writer.py
│   │   ├── reviewer.py
│   │   ├── editor.py               # v2 新增
│   │   ├── distributor.py
│   │   ├── analyst.py
│   │   └── shared/
│   │       ├── koc_persona.py      # KOC 人设 prompt 片段
│   │       └── chinese_hooks.py    # 中文爆款基因
│   │
│   ├── graph/                      # LangGraph 编排
│   │   ├── __init__.py
│   │   ├── state.py                # 共享 State（v2 含 revision_count）
│   │   ├── nodes.py                # 节点函数（含 @log_work 装饰器）
│   │   ├── edges.py                # 条件边（v2 含审改循环 + fan-out）
│   │   └── builder.py              # build_graph() 工厂
│   │
│   ├── sources/                    # 信息源采集
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── arxiv.py                # 真爬虫
│   │   ├── hackernews.py           # 真爬虫
│   │   ├── github_trending.py      # 真爬虫
│   │   ├── reddit.py               # 真爬虫（需 PRAW key）
│   │   ├── mock_xiaohongshu.py     # mock
│   │   ├── mock_douyin.py          # mock
│   │   └── mock_x.py               # mock
│   │
│   ├── visual/                     # 图生成三轨
│   │   ├── __init__.py
│   │   ├── text_card.py            # HTML 模板 + Playwright
│   │   ├── infographic.py          # SVG 模板
│   │   ├── ai_image.py             # 即梦 API
│   │   └── templates/
│   │       ├── card_white.html
│   │       ├── card_dark.html
│   │       ├── card_emoji.html
│   │       └── infographic_compare.svg
│   │
│   ├── llm/                        # LLM 客户端封装
│   │   ├── __init__.py
│   │   └── client.py               # ChatOpenAI 指向火山方舟
│   │
│   ├── storage/                    # ⭐ v2 存储抽象
│   │   ├── __init__.py
│   │   ├── interface.py            # BaseStorage 抽象基类
│   │   ├── doc_interface.py        # DocStorage 抽象基类（v2 新增）
│   │   └── id_generator.py         # 业务 ID 生成器
│   │
│   ├── decorators/                 # ⭐ v2 装饰器
│   │   ├── __init__.py
│   │   └── log_work.py             # @log_work 自动写工作日志
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config.py
│
├── feishu_adapter/                 # ★ 飞书适配层（v2 双栈）
│   ├── __init__.py
│   │
│   ├── base/                       # ⭐ 多维表格适配
│   │   ├── __init__.py
│   │   ├── client.py               # lark-oapi Bitable 封装
│   │   ├── feishu_storage.py       # 实现 BaseStorage 接口
│   │   ├── id_mapping.py           # 业务 ID ↔ 飞书 record_id 映射
│   │   ├── tables.py               # ⭐ 7 张表 schema 定义
│   │   └── views.py                # 看板视图、分组视图配置
│   │
│   ├── docs/                       # ⭐ v2 飞书文档适配
│   │   ├── __init__.py
│   │   ├── client.py               # lark-oapi Docs 封装
│   │   ├── feishu_doc_storage.py   # 实现 DocStorage 接口
│   │   ├── markdown_to_blocks.py   # ⭐ MD → 飞书 block 转换器
│   │   ├── doc_templates.py        # 4 类文档的结构模板
│   │   └── folder_manager.py       # 文件夹创建与权限管理
│   │
│   └── _archived/                  # v1 归档
│       └── tables_v1.py            # v1 的 11 张表（已废弃）
│
├── seed/                           # 种子数据
│   ├── koc_persona.yaml            # KOC-001 学AI的刘同学
│   ├── employees_v2.yaml           # 9 位 Agent（v2 阵容）
│   └── sources.yaml                # 7 个信源
│
├── mock_data/                      # mock 数据集
│   ├── xiaohongshu_hot.json        # 小红书爆款样本
│   ├── douyin_hot.json
│   ├── x_hot.json
│   └── analytics_mock.json         # ⭐ v2 新增：数据回流 mock
│
├── tests/                          # 测试
│   ├── test_lark_hello.py          # ✅ 已通过
│   ├── test_lark_complete.py       # ✅ 已通过
│   ├── test_doubao_hello.py        # ✅ 已通过
│   ├── test_graph_hello.py         # ✅ 已通过
│   ├── test_bitable_full.py        # ✅ 已通过
│   ├── test_lark_doc_hello.py      # ⭐ v2 新增：飞书文档 SDK 验证
│   ├── test_field_types_smoke.py   # ⭐ v2 新增：字段类型映射验证
│   ├── test_storage_interface.py   # ⭐ v2 新增：存储接口测试
│   ├── test_trend_scout_e2e.py     # ⭐ 端到端：小哨跑通
│   └── test_full_pipeline_smoke.py # ⭐ 端到端：完整流程冒烟
│
├── demo/                           # Demo 物料
│   ├── screenshots/
│   ├── walkthrough.md              # 演示讲解稿
│   └── recording_script.md         # 录屏脚本
│
└── docs/                           # 文档（v2 完整目录）
    ├── VERSION.md                  # 当前架构版本说明
    │
    ├── NewsAI_project_v2.md        # ⭐ v2 项目书
    ├── NewsAI_workspace_v2.md      # ⭐ v2 仓库结构（本文件）
    ├── Tables_schema_v2.md         # ⭐ 7 张表字段定义
    ├── Documents_design_v2.md      # ⭐ 4 类文档设计
    ├── Agent_roster_v2.md          # ⭐ 9 位 Agent 种子数据
    │
    ├── KOC_persona.md              # KOC 人设（v2 仍适用）
    ├── Context.md                  # 工作上下文
    ├── SOP.md                      # 开发 SOP
    ├── Feishu_Base_API_Guide.md    # 飞书 API 参考
    ├── FeishuBase_Usage_Examples.md # 飞书使用示例
    │
    ├── architecture.md             # 架构详解（评委深读）
    ├── prompts_design.md           # Prompt 设计思路
    └── lark_api_notes.md           # 飞书 API 踩坑记录
    
    ├── NewsAI_project_v1_deprecated.md       # v1 归档
    ├── NewsAI_workspace_v1_deprecated.md     # v1 归档
    ├── Tables_schema_v1_deprecated.md        # v1 归档
    └── Agent_roster_v1_deprecated.md         # v1 归档
```

---

## 三、核心模块说明

### 3.1 `core/storage/` —— v2 双重存储抽象 ⭐

v2 引入两个抽象基类：

```python
# core/storage/interface.py
class BaseStorage(ABC):
    """多维表格存储接口（v1 已存在，v2 微调）"""
    @abstractmethod
    def create(self, table: str, fields: dict) -> str: ...
    @abstractmethod
    def update(self, table: str, business_id: str, fields: dict): ...
    @abstractmethod
    def query(self, table: str, filter_: dict = None) -> list[dict]: ...
    @abstractmethod
    def delete(self, table: str, business_id: str): ...

# core/storage/doc_interface.py（v2 新增）
class DocStorage(ABC):
    """飞书文档存储接口"""
    @abstractmethod
    def create_doc(self, title: str, folder: str, content_md: str) -> dict:
        """创建文档，返回 {doc_token, share_url}"""
        ...
    @abstractmethod
    def append_section(self, doc_token: str, section_title: str, content_md: str):
        """追加章节到文档末尾（用于审改循环、经验文档增量）"""
        ...
    @abstractmethod
    def get_share_url(self, doc_token: str) -> str: ...
    @abstractmethod
    def set_permissions(self, doc_token: str, user_ids: list[str]): ...
```

**Agent 通过依赖注入接收两个接口实例**，不知道底层是飞书还是其他。

### 3.2 `feishu_adapter/base/` —— 多维表格实现

`feishu_storage.py` 实现 `BaseStorage` 接口，调用 lark-oapi Bitable。

**关键设计**：
- `id_mapping.py` 内部维护 `{业务ID -> 飞书record_id}` 映射
- 业务代码全程只用业务 ID，飞书 record_id 是 FeishuStorage 的内部细节

### 3.3 `feishu_adapter/docs/` —— 飞书文档实现 ⭐ v2 新增

`feishu_doc_storage.py` 实现 `DocStorage` 接口，调用 lark-oapi Docs。

**核心难点**：飞书文档 API 不直接接受 markdown 字符串，需要 `markdown_to_blocks.py` 转换器：

```python
# feishu_adapter/docs/markdown_to_blocks.py
def markdown_to_lark_blocks(md: str) -> list[dict]:
    """
    输入：标准 markdown 字符串
    输出：飞书文档 block 列表
    
    支持：
    - H1/H2/H3 → heading1/2/3 block
    - 段落 → paragraph block
    - 无序列表 → bullet block
    - 有序列表 → ordered block
    - 代码块 → code block
    - 引用 → quote block
    - 表格 → table block
    - 图片占位 → image placeholder block
    """
```

> ⚠️ **关键风险**：转换器实现复杂度可能高。MVP 阶段降级方案：使用 lark-oapi 的"文档基础块"逐段写入，每个 H2 章节一次 API 调用。

### 3.4 `core/decorators/log_work.py` —— v2 装饰器

```python
@log_work
def trend_scout_node(state: State) -> State:
    """节点函数挂上 @log_work，自动写入 Agent协作日志 表"""
    ...
```

装饰器自动：
- 记录开始时间
- 捕获异常
- 记录结束时间
- 调用 storage.create("Agent协作日志", {...}) 写入字节风格日报

### 3.5 `core/graph/` —— v2 编排升级

#### state.py（v2 升级）

```python
@dataclass
class State:
    # v1 字段
    topic_id: str
    
    # v2 新增字段
    revision_count: int = 0      # 审改轮次
    review_verdict: str = None   # pass / needs_revision
    audit_doc_token: str = None  # 审改文档 token
    
    # 各 Agent 产出引用
    trend_ids: list[str] = field(default_factory=list)
    post_doc_url: str = None
    script_doc_url: str = None
    distribution_plan: dict = None
```

#### builder.py（v2 升级）

```python
def build_graph():
    g = StateGraph(State)
    
    # Linear: 信息 → 决策
    g.add_edge("trend_scout", "topic_curator")
    
    # Fan-out: 决策 → 生产组并发
    g.add_edge("topic_curator", "content_writer")
    g.add_edge("topic_curator", "visual_designer")
    g.add_edge("topic_curator", "script_writer")
    
    # Fan-in: 生产组 → 治理组
    g.add_edge(["content_writer", "visual_designer", "script_writer"], "reviewer")
    
    # ⭐ Cyclic: 审改循环
    g.add_conditional_edges(
        "reviewer",
        lambda state: "editor" if state.review_verdict == "needs_revision"
                                  and state.revision_count < MAX_REVISIONS
                      else "distributor",
    )
    g.add_edge("editor", "reviewer")  # 改完回到审
    
    # Linear: 分发 → 复盘
    g.add_edge("distributor", "analyst")
    
    return g.compile()
```

### 3.6 `bootstrap.py` —— 一键复现入口

```python
def bootstrap():
    """
    1. 读取 .env 配置
    2. 创建多维表格 App（如不存在）
    3. 批量建表（7 张业务表）
    4. 创建飞书文档文件夹（NewsAI产物/帖子, 视频脚本, 审改, 经验）
    5. 写入种子数据：
       - KOC-001 学AI的刘同学
       - 9 位 Agent 花名册
       - 7 个信源配置
    6. 跑一次完整 LangGraph 流程（端到端冒烟）
    7. 打印链接：
       - Base 链接
       - 文档目录链接
       - 4 类产出文档示例链接
    8. 设置评委权限（如配置）
    """
```

### 3.7 `run.py` —— 日常使用入口

```bash
python run.py --once              # 跑一轮
python run.py --watch             # 持续运行（cron 模式）
python run.py --agent topic       # 单独跑某个 Agent（调试）
python run.py --resume <topic_id> # 恢复某个选题的流程
```

---

## 四、技术栈

### 4.1 核心依赖

| 库 | 版本 | 用途 | v2 变化 |
|---|---|---|---|
| `python` | 3.11 | 主语言 | — |
| `langgraph` | latest | Agent 编排 | — |
| `langchain` | latest | LLM 抽象 + Tools | — |
| `langchain-openai` | latest | LLM 客户端 | — |
| `lark-oapi` | latest | 飞书 SDK（Base + Docs） | **v2 用 Docs API** |
| `pydantic` | v2 | 数据模型 | — |
| `python-dotenv` | latest | 环境变量 | — |
| `playwright` | latest | HTML → 图片 | — |
| `httpx` | latest | HTTP 客户端 | — |
| `feedparser` | latest | RSS / Atom | — |
| `praw` | latest | Reddit API | — |
| `loguru` | latest | 日志 | — |
| `markdown` | latest | ⭐ v2 新增：markdown 解析（用于 → 飞书 block）| — |

### 4.2 不引入的东西（避免过度设计）

- ❌ FastAPI / Flask —— NewsAI 不需要 web 后端
- ❌ Redis / Celery —— LangGraph 已够用
- ❌ Docker —— bootstrap 直接 pip 跑
- ❌ pytest 完整矩阵 —— 只写关键冒烟测试
- ❌ Plugin 系统 —— hardcode 9 Agent 不预留扩展

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
LARK_DOCS_FOLDER_TOKEN=          # ⭐ v2 新增：NewsAI产物 文件夹 token

# ===== 即梦图像 =====
JIMENG_API_KEY=                  # 选填

# ===== Reddit =====
REDDIT_CLIENT_ID=                # 选填
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=newsai/0.2

# ===== 评委权限（选填）=====
JUDGE_USER_IDS=                  # 评委的飞书 user_id，逗号分隔

# ===== 运行配置 =====
KOC_PERSONA_ID=KOC-001
MAX_REVISIONS=3                  # ⭐ v2 新增：审改最大轮次
LOG_LEVEL=INFO
```

---

## 五、运行方式

### 5.1 评委一键复现

```bash
git clone https://github.com/Vendow-ZQ/NewsAI.git
cd NewsAI

pip install -e .
playwright install chromium

cp .env.example .env
# 编辑 .env，填入 LARK 和 LLM 的 key

python bootstrap.py

# 命令行打印 Base + 文档库链接
# 浏览器打开即可看到完整虚拟组织
```

### 5.2 本地开发

```bash
# 单独跑某个 Agent（调试 prompt）
python run.py --agent reviewer

# 端到端跑一次（写入真实 Base + 真实文档）
python run.py --once

# 看日志
tail -f logs/newsai.log
```

---

## 六、开发里程碑（v2 推进计划）

> 当前时间：2026-05-04 18:30 SGT
> 飞书截止：2026-05-07 12:00（约 42 小时）
> PCG 截止：2026-05-06 23:59（约 30 小时）

| 阶段 | 时间窗 | 目标 | 完成标志 |
|---|---|---|---|
| ✅ Stage 1 | 5/3 完成 | hello world 三件套 | 飞书 + 豆包 + LangGraph 跑通 |
| ✅ Stage 1.5 | 5/4 18:00 | v1 → v2 文档归档 | 4 份 v1 加 _deprecated 后缀 |
| 🔄 **Stage 2** | 5/4 晚 | **飞书文档 SDK 验证** | test_lark_doc_hello 跑通 |
| Stage 3 | 5/5 上午 | Storage 双接口实现 | BaseStorage + DocStorage 跑通 |
| Stage 4 | 5/5 下午 | BaseAgent 模板 + 小哨端到端 | test_trend_scout_e2e 通过 |
| Stage 5 | 5/5 晚 | 其他 8 个 Agent 铺开 | 端到端 9 节点跑通 |
| Stage 6 | 5/6 上午 | 审改循环 + 文档生成 | 审改文档累积 3 轮通过 |
| Stage 7 | 5/6 下午 | bootstrap 完整化 + 视图美化 | 一键复现 demo 完整 |
| Stage 8 | 5/6 晚 | TrendAI 同步 + PCG 提交 | PCG 截止前提交 |
| Stage 9 | 5/7 上午 | 录屏 + PDF 文档 + 飞书提交 | 飞书截止前提交 |

---

## 七、风险点与对策

| 风险 | 对策 | 优先级 |
|---|---|---|
| **飞书文档 SDK 不直接支持 markdown** | 写转换器；降级用 block 逐段调用 | 🔴 P0，今晚验证 |
| markdown → block 转换器复杂 | 只支持核心 markdown 语法（H1-3、段落、列表、代码块），其他降级 | 🔴 P0 |
| 审改循环可能死循环 | hardcode `MAX_REVISIONS=3` + 容错处理 | 🟡 P1 |
| 多文档创建拖慢流程 | 异步并发创建（asyncio）| 🟢 P2 |
| 9 个 Agent 全跑通耗时 | 单条 demo 限制信息源 5 条以内 | 🟢 P2 |
| Token 烧得快 | 每个 Agent 单次调用 token 上限 4000 | 🟢 P2 |
| Reddit PRAW key 没申请 | 默认禁用，只用 arXiv + HN + GitHub 三源 | 🟢 P2 |
| 评委权限配置复杂 | 默认链接可访问；评委 user_id 选填 | 🟢 P2 |

---

## 八、与 TrendAI（PCG 赛事）的关系

**v2 阶段 TrendAI 处于冻结状态**。NewsAI 跑通后再做 TrendAI 的迁移：

```
最后 6 小时 TrendAI 冲刺：
1. 复制 NewsAI/core/ → TrendAI/core/
2. 改 adapter：feishu → local（JSON 文件）
3. 改 doc_storage：飞书文档 → 本地 markdown 文件
4. 极简 React 前端（Home page + Workspace page）
5. 部署到 Vercel
6. 录屏 + PDF
7. 提交 PCG
```

**不强求两边互通**，TrendAI 作为"NewsAI 同源衍生"提交。

---

## 九、附录：v2 技术选型决策记录

### 决策 1：用 lark-oapi 而非 CLI
- 黄梦轩老师推荐 CLI，但 SDK 工程上更稳
- 错误处理、类型安全、错误码封装都更好

### 决策 2：markdown 转换器自研，不引入第三方库
- 第三方库（如 mistune）输出格式与飞书 block 差异大
- 自研只支持核心语法，可控且足够

### 决策 3：审改文档累积式追加，不分多个文档
- 单文档可见演进过程
- 评委体验最佳

### 决策 4：4 平台内容写在 1 个帖子文档里
- 详见 Documents_design_v2.md Flag 1

### 决策 5：v2 不做 _core_master 同步机制
- 黑客松场景下复制粘贴比 git submodule 简单
- TrendAI 最后冲刺时直接复制

### 决策 6：bootstrap 不强制部署
- 评委本地跑即可
- 不依赖 Vercel / Railway 等部署
