# NewsAI + TrendAI 开发SOP

> 版本：v1.1  
> 时间：2026-05-03 → 2026-05-05（48小时冲刺版）  
> 原则：**先跑通，再抛光。没写的功能都砍。**  
> 更新：Schema已定稿，Stage 0完成，进入Stage 1

---

## 一、总目标

**两个比赛，一套Core，各配一个Adapter，都跑得通。**

| 项目 | 截止 | 必须交付 | Nice to have |
|------|------|----------|--------------|
| NewsAI | 5/7 12:00 | 飞书Base 11张表 + 9个Agent串通 + bootstrap.py一键跑通 | 视图美化、演示视频 |
| TrendAI | 5/6 23:59 | 本地JSON存储 + 极简UI(1按钮3区块) + 工作台UI(可选) | 部署链接、演示视频 |

**不做（防过度设计）**：
- Docker/Redis/Celery/Postgres
- 复杂前端（Next.js/shadcn/Redux）
- 完整测试矩阵（只跑冒烟测试）
- 视频生成功能（只出脚本，不生成视频文件）
- 实时WebSocket（用2秒轮询）

---

## 二、阶段目标与依赖

### Stage 0: 拍板Schema（5/3晚）✅ 已完成

**任务**：ZQ确认`Tables_schema.md`中的8张业务表字段

**决策记录**（已更新到文档）：
1. ✅ 信息源配置用短ID（SRC-001）
2. ✅ 热帖池需要去重，多源放两个超链接
3. ✅ 选题库状态加"已发布"
4. ✅ 内容稿件平台版本用子字段存储
5. ✅ 审查记录多轮修改多记录
6. ✅ 数据回流先用mock

**输出**：`Tables_schema.md` 定稿

**状态**：✅ 已解锁Stage 1

---

### 📅 48小时冲刺计划（5/4-5/5）

**每日工时**：10小时（8-12, 14-18, 20-22）

| 日期 | 上午(4h) | 下午(4h) | 晚上(2h) |
|------|----------|----------|----------|
| 5/4 | Stage 1: 基建+Hello World | Stage 2: 爬虫(2真源) | - |
| 5/5 | Stage 3: Agent主线(小编→小文→小图→小审→小发) | Stage 4: Graph串线 | 视频+提交 |

**砍掉的功能**：小数、小析深度分析、GitHub/Reddit真源、小播(TrendAI)、工作台UI、视图美化

**底线必须通**：小哨→小编→小文→小审→小发

---

### Stage 1: 基建联通（5/4上午）🔧 必须串行

**三件事，一件不通后面的全废**：

| 序号 | 任务 | 做什么 | 输出 | 测试标准 |
|------|------|--------|------|----------|
| 1.1 | Hello World 1: 飞书联通 | 用lark-oapi SDK在飞书建1张测试表，写1条记录，读出来 | `tests/test_lark_hello.py` | ✅ 已完成 |
| 1.2 | Hello World 2: LLM联通 | 用langchain-openai调Doubao，问"你好"，拿到回复 | `tests/test_doubao_hello.py` | ✅ 已完成 |
| 1.3 | Hello World 3: LangGraph联通 | 2个节点：A节点调LLM生成文字 → B节点打印文字 | `tests/test_graph_hello.py` | ✅ 已完成 |

**扩展测试**（权限开通后完成）：
- ✅ `tests/test_bitable_full.py`: 创建表、重命名表、字段CRUD、写入mock数据全部通过

**Stage 1 交付物**（为后续Agent开发准备）：
- ✅ `core/utils/feishu_base.py`: FeishuBaseManager 封装类（15+方法）
- ✅ `docs/Feishu_Base_API_Guide.md`: 完整API操作手册（含错误码）
- ✅ `docs/FeishuBase_Usage_Examples.md`: Agent开发示例代码

**依赖**：Stage 0完成（有表结构才知道建什么表）

**并行策略**：1.1/1.2/1.3 可以同时进行（互不依赖），但都必须在1.4前完成

| 1.4 | bootstrap.py | 一键完成：①建11张表 ②写种子数据(KOC+9员工+信息源) ③跑冒烟测试 | `bootstrap.py` | 运行结束打印：`✅ Base链接: https://...` |

---

### Stage 2: 爬虫开发（5/4下午）🕷️ 4真3假

**策略**：4个真爬虫（开发成本低）+ 3个mock（反爬强，直接假数据）

| 源 | 类型 | 实现方式 | 输出文件 | 测试标准 | 并行 |
|----|------|----------|----------|----------|------|
| arXiv | 真 | 官方API（5行代码） | `sources/arxiv.py` | 能抓10条论文标题 | ✅ 可并行 |
| HackerNews | 真 | Firebase API（官方） | `sources/hackernews.py` | 能抓top10故事 | ✅ 可并行 |
| GitHub Trending | 真 | 简单爬虫/非官方RSS | `sources/github_trending.py` | 能抓当日热榜 | ✅ 可并行 |
| Reddit | 真? | PRAW库（需你申请key） | `sources/reddit.py` | 能抓r/LocalLLaMA热帖 | ✅ 可并行 |
| 小红书 | Mock | 读本地JSON文件 | `sources/mock_xiaohongshu.py` | 返回5条假热帖 | ✅ 可并行 |
| 抖音 | Mock | 读本地JSON文件 | `sources/mock_douyin.py` | 返回5条假热帖 | ✅ 可并行 |
| X/Twitter | Mock | 读本地JSON文件 | `sources/mock_x.py` | 返回5条假热帖 | ✅ 可并行 |

**Mock数据来源**：你手抄5-10条真实爆款（比AI硬编真实），存`mock_data/*.json`

**Stage 2验收**：运行`python -m tests.test_sources`，看到`7源全部通过`

---

### Stage 3: CodingAgent开发（5/5全天）🤖 核心工程

**9个Agent，3条并行线**：

```
线A（数据采集团）：小哨 + 小析
线B（内容创作团）：小编 + 小文 + 小图 + 小播  
线C（运营审核团）：小审 + 小发 + 小数
```

#### Agent流水线（StateGraph节点）

```
小哨(trend_scout) 
    ↓ [并发：爬完N个源汇总]
小析(hook_analyst)
    ↓ [串行：必须分析完才能选]
小编(topic_curator) ← 决策节点，核心 bottleneck
    ↓ [并发：3人同时写]
    ├→ 小文(content_writer) → 写公众号/小红书/抖音/B站 4版本
    ├→ 小图(visual_designer) → 生成文字卡片/信息图/prompt
    └→ 小播(script_writer) → 写抖音/B站脚本（TrendAI演示时跳过此节点）
    ↓ [全部写完才能审]
小审(reviewer)
    ↓ [串行：过审才能发]
小发(distributor)
    ↓ [后台异步]
小数(analyst)
```

#### 每个Agent的标准结构

```python
# 统一模板，所有Agent照这个写
class XxxAgent(BaseAgent):
    name = "中文花名"
    english_name = "XxxAgent" 
    emoji = "🔍"
    
    def run(self, state):
        # 1. 读KOC人设（L1真源）
        koc = storage.get("KOC人设", "KOC-001")
        
        # 2. 读输入（上游Agent产出）
        input_data = state["上游表名"]
        
        # 3. 拼Prompt（KOC人设 + 自己的system prompt）
        prompt = f"""
        你是{self.name}，为KOC【{koc.账号名}】工作。
        KOC定位：{koc.一句话定位}
        你的职责：{self.description}
        """
        
        # 4. 调LLM干活
        result = llm.generate(prompt, input_data)
        
        # 5. 写输出表（下游Agent读取）
        record_id = storage.create("下游表名", result)
        
        # 6. 写工作日志（自动）
        log_work(self.name, "任务类型", input_refs=[], output_refs=[record_id])
        
        # 7. 更新state给Graph
        state["当前产出"] = result
        return state
```

#### Stage 3开发顺序（重要！）

**Day 1（5/5上午）：线B先做（内容创作团）**
- 原因：内容产出是评委最直接看到的，Demo时只跑这一截也能唬住人
- 小编 → 小文 → 小图（小播可选）
- **验收标准**：输入一个选题标题，输出一篇完整文章+配图

**Day 2（5/5下午）：线A + 线C补齐**
- 小哨 + 小析（让选题有数据来源）
- 小审 + 小发（让内容能过审发布）
- 小数（后台跑，优先级最低）

**并行策略**：
- 我可以同时写3个Agent（3条线各1个）
- 但你测试时按线测：先测线B跑通，再测线A，最后线C

---

### Stage 4: StateGraph串线（5/6上午）🔗

**任务**：用LangGraph把9个Agent串成图

**文件**：`core/graph/builder.py`

**Graph结构**：

```python
# 简化版，先串再优化并发
graph = StateGraph(State)

# 第一层：采集（并发节点）
graph.add_node("scout", trend_scout_node)

# 第二层：分析
graph.add_node("analyze", hook_analyst_node)
graph.add_edge("scout", "analyze")

# 第三层：选题（决策节点）
graph.add_node("curate", topic_curator_node)
graph.add_edge("analyze", "curate")

# 第四层：创作（并发节点）
graph.add_node("write", content_writer_node)
graph.add_node("design", visual_designer_node)
graph.add_node("script", script_writer_node)
graph.add_edge("curate", "write")
graph.add_edge("curate", "design")
graph.add_edge("curate", "script")

# 第五层：审核（合并节点）
graph.add_node("review", reviewer_node)
graph.add_edge(["write", "design", "script"], "review")  # 等3人都完

# 第六层：分发
graph.add_node("distribute", distributor_node)
graph.add_edge("review", "distribute")

# 入口
graph.set_entry_point("scout")
```

**测试标准**：
- `python run.py --mode single`：单步调试，每个节点能停能看
- `python run.py --mode full`：全自动跑完，从爬到发一气呵成

---

### Stage 5: 分叉交付（5/6下午 → 5/7中午）🚀

#### 5A: NewsAI线（飞书）

| 时间 | 任务 | 产出 | 验收 |
|------|------|------|------|
| 5/6下午 | bootstrap.py最终版 | 一键跑通 | 新人5分钟能复现 |
| 5/6晚上 | 飞书Base视图美化 | 看板视图 | 一眼看清虚拟组织架构 |
| 5/7上午 | 录演示视频 | ≤3分钟MP4 | 展示完整流程 |
| 5/7 12:00 | 提交 | GitHub链接 | Public仓库 |

#### 5B: TrendAI线（本地+前端）

| 时间 | 任务 | 产出 | 验收 |
|------|------|------|------|
| 5/6下午 | FastAPI接口 | `/workflow/run`能调通 | Postman测试通过 |
| 5/6下午 | 极简UI | 1按钮+3区块 | 点击→等10秒→出结果 |
| 5/6晚上 | 部署 | Vercel链接 | 外网可访问 |
| 5/6 23:59 | 提交 | GitHub + Vercel链接 | - |

**分叉点**：从Stage 4结束开始，NewsAI和TrendAI完全分开，互不依赖。

---

## 三、CodingAgent并行分工表

假设启动多个CodingAgent（或我一个人模拟多线程），分工如下：

### Agent 1: 基建组（Stage 1）
- **负责**：Schema代码 + 飞书联通 + bootstrap.py
- **读**：`Tables_schema.md` + `KOC_persona.md`
- **写**：`feishu_adapter/schemas/tables.py`, `bootstrap.py`
- **阻塞**：必须等ZQ拍板Schema

### Agent 2: 爬虫组（Stage 2）  
- **负责**：7个数据源（4真3假）
- **读**：`sources/base.py` + 各平台API文档
- **写**：`sources/*.py`
- **阻塞**：无（只要Stage 0完成）
- **并行**：7个源可以7个人同时写

### Agent 3: 内容创作组（Stage 3 - 线B）
- **负责**：小编 + 小文 + 小图
- **读**：`KOC_persona.md`（宪法）+ `Agent_roster.md`（角色）
- **写**：`agents/topic_curator.py`, `agents/content_writer.py`, `agents/visual_designer.py`
- **阻塞**：Stage 1完成（有表存数据）
- **关键路径**：**优先做！**

### Agent 4: 运营审核组（Stage 3 - 线C）
- **负责**：小审 + 小发 + 小数
- **读**：`KOC_persona.md`（禁区话题）+ `Agent_roster.md`
- **写**：`agents/reviewer.py`, `agents/distributor.py`, `agents/analyst.py`
- **阻塞**：Agent 3完成（有内容可审）

### Agent 5: 数据采集组（Stage 3 - 线A）
- **负责**：小哨 + 小析
- **读**：`KOC_persona.md`（领域偏好）+ 爬虫产出
- **写**：`agents/trend_scout.py`, `agents/hook_analyst.py`
- **阻塞**：Stage 2完成（有数据源）

### Agent 6: Graph组（Stage 4）
- **负责**：StateGraph串联 + 并发节点优化
- **读**：9个Agent的输入输出接口
- **写**：`graph/builder.py`, `graph/nodes.py`, `graph/edges.py`
- **阻塞**：Stage 3完成（有节点可串）

### Agent 7: NewsAI交付组（Stage 5A）
- **负责**：bootstrap.py最终版 + 飞书视图 + 演示视频
- **阻塞**：Stage 4完成

### Agent 8: TrendAI交付组（Stage 5B）
- **负责**：LocalStorage + FastAPI + React前端 + 部署
- **阻塞**：Stage 4完成

---

## 四、验收成果清单

每个Stage结束必须过验收，不过不能进下一阶段。

### Stage 0 验收
- [ ] `Tables_schema.md` 末尾10个问题都有ZQ回复
- [ ] 你回复"按这个做"或"改成XXX"

### Stage 1 验收（3个Hello World）
- [ ] `python tests/test_lark_hello.py` → 打印"飞书联通成功"
- [ ] `python tests/test_doubao_hello.py` → 打印模型回复
- [ ] `python tests/test_graph_hello.py` → 打印2节点输出
- [ ] `python bootstrap.py` → 打印11张表创建成功 + Base链接

### Stage 2 验收（爬虫）
- [ ] `python -m tests.test_sources` → 7/7通过
- [ ] `mock_data/` 下有3个JSON文件（小红书/抖音/X各5条）

### Stage 3 验收（Agent）
- [ ] 小编→小文→小图能跑通：输入选题→输出文章+图
- [ ] 小审能审：输入文章→输出过/不过+修改建议
- [ ] 小哨→小析能跑通：输入关键词→输出爆点分析

### Stage 4 验收（Graph）
- [ ] `python run.py --mode single` 能单步调试
- [ ] `python run.py --mode full` 能从零跑完全程
- [ ] 全流程耗时<5分钟（本地测试）

### Stage 5A 验收（NewsAI交付）
- [ ] 新开一台电脑，`git clone` + `python bootstrap.py` 5分钟内跑通
- [ ] 飞书Base能看到11张表，数据完整
- [ ] 演示视频≤3分钟，展示完整流程

### Stage 5B 验收（TrendAI交付）
- [ ] Vercel链接外网可访问
- [ ] 点击大按钮，10秒内出选题+内容
- [ ] 工作台模式能看到Agent日志

---

## 五、Git策略

### 分支模型（极简）

```
main 分支：始终可运行
    │
    ├── feature/storage  （Stage 1，我单独推）
    ├── feature/sources  （Stage 2，可并行）
    ├── feature/agents   （Stage 3，按线分批推）
    ├── feature/graph    （Stage 4，等Agent合完）
    └── feature/ui       （Stage 5B，TrendAI专用）
```

### Push节奏

| 时间 | 动作 | 说明 |
|------|------|------|
| 每Stage完成 | 推该Stage代码 | 不push半成品 |
| 每天结束 | 推`worklog.md` | 记录当天进展 |
| Stage 4结束 | 打Tag `v0.9-core` | Core冻结，开始分叉 |
| 最终提交 | 推`main`分支 | Public仓库 |

### Commit消息格式

```
[Stage] 模块: 做了什么

例：
[Stage 1] storage: 添加FeishuStorage实现
[Stage 3] agent: 小编选题Agent跑通
[Stage 5A] bootstrap: 一键初始化完成
```

---

## 六、每日站会（自问自答）

每天结束时，ZQ问Claude Code这3个问题：

1. **今天完成了哪个Stage的什么任务？**（看产出，不看工时）
2. **明天必须完成什么，否则赶不上截止？**（识别阻塞点）
3. **有什么需要我决定或提供资源的？**（Reddit key？爆款样例？）

---

## 七、紧急砍需求预案

如果时间不够，按这个顺序砍：

1. **砍小数**（数据复盘Agent）：最不重要，后台跑不跑都行
2. **砍小播在TrendAI**：演示时只跑图文，不写视频脚本
3. **砍工作台UI**：极简模式能跑就行
4. **砍3个mock源**：只跑arXiv+HackerNews两个真源
5. **砍视图美化**：表能存数据就行，不看板

**底线（绝对不能砍）**：
- 小哨→小编→小文→小审→小发 这条主线必须通（小析可简化）
- bootstrap.py必须能跑
- 飞书Base/本地JSON必须能存数据

---

## 八、子Agent并行开发Prompt

用于启动多个CodingAgent并行工作，每个Agent读对应文档，独立产出。

```markdown
# CodingAgent 任务指令

你是【{Agent角色}】，负责开发NewsAI/TrendAI项目的【{具体模块}】。

## 📋 任务概览

| 项目 | 内容 |
|------|------|
| 你的角色 | {Agent角色} |
| 负责模块 | {文件路径} |
| 依赖前置 | {前置条件} |
| 阻塞后置 | {谁依赖你} |
| 交付时间 | {截止时间} |

## 📖 必读文档（按优先级）

### L1 真理来源（必须读）
1. `docs/Tables_schema.md` → 看第{X}章（{表名}）的字段定义
2. `docs/KOC_persona.md` → 看{相关模块}，了解KOC人设如何影响本模块
3. `docs/Agent_roster.md` → 看{Agent名}的角色定义（第{X}章）

### L2 项目定位（参考读）
4. `docs/NewsAI_workspace.md` → 看技术栈和目录结构
5. `docs/SOP.md` → 看Stage {X}的验收标准

### L3 代码参考（如有）
6. `core/agents/base.py` → Agent基类定义
7. `core/storage/interface.py` → Storage接口定义

## 🎯 核心任务

{详细任务描述}

### 输入（从state或storage读）
- `{输入字段1}`: {来源表，如TOPIC-20260504-001}
- `{输入字段2}`: {来源Agent，如小编}

### 处理逻辑
1. {步骤1}
2. {步骤2}
3. {步骤3}

### 输出（写入state和storage）
- **写表**: `{表名}`（{表前缀}-YYYYMMDD-NNN格式）
- **写字段**: 
  - `{字段1}`: {说明}
  - `{字段2}`: {说明}
- **写LOG**: 自动（用@log_work装饰器）

## 🚫 禁止做的事

- 不要改其他Agent的代码
- 不要改core/storage/interface.py（只调用）
- 不要引入新依赖（用已有的llm_client, storage）
- 不要写复杂错误处理（try/except包一层即可）

## ✅ 验收标准

跑通这个测试即算完成：

```python
# tests/test_{你的模块}.py
from core.agents.{你的agent} import {AgentClass}

agent = {AgentClass}(storage=mock_storage, llm=mock_llm)
state = {{"输入": "测试数据"}}
result = agent.run(state)

assert "输出字段" in result
assert storage.exists("{表名}", result["id"])
print("✅ {Agent名} 通过")
```

## 📤 交付物

1. **代码文件**: `{文件路径}`（完整实现）
2. **测试文件**: `tests/test_{模块}.py`（冒烟测试）
3. **更新日志**: 在`worklog.md`写一行：`- [{时间}] {Agent名}完成，产出{X}条测试数据`

## 🆘 遇到阻塞

如果：
- 发现Schema字段缺失 → **立即停止**，在`worklog.md`标记`[阻塞] Schema问题`
- 依赖的Agent接口不对 → **立即停止**，标记`[阻塞] 接口不匹配`
- 不知道KOC人设怎么用 → 读`KOC_persona.md`第4节"Agent读取人设的范式"

**不要猜测，不要绕过，立即上报阻塞。**

---

**开始工作前，确认你已读完L1文档。回复"已读，开始工作"。**
```

### 使用示例：启动3个Agent并行

**Agent A - 基建组**：
- 角色：基建组Agent
- 模块：`feishu_adapter/schemas/tables.py`
- 读：Tables_schema.md（全部8张表）
- 做：把md里的表定义转成Python Pydantic类

**Agent B - 爬虫组**：
- 角色：爬虫组Agent  
- 模块：`sources/arxiv.py`, `sources/hackernews.py`
- 读：NewsAI_workspace.md（技术栈）+ arXiv API文档
- 做：两个真爬虫，能抓10条数据

**Agent C - 内容组**：
- 角色：内容创作组Agent
- 模块：`agents/content_writer.py`
- 读：KOC_persona.md（语气/结构）+ Agent_roster.md（小文角色）
- 做：写小文Agent，输入选题→输出4平台文章

**并行规则**：
- A/B/C同时启动，互不等待
- 但C需要等A完成表结构才能测试（可以先写代码，等A）
- 每天22:00检查：谁阻塞了谁，调整优先级

---

*SOP v1.1 更新完成，Schema已定稿，等待启动Stage 1。*