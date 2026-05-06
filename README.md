# NewsAI - AI 新闻编辑部

**飞书 AI 校园挑战赛参赛作品**
> 跑在飞书多维表格上的 AI 新闻编辑部

## 一句话介绍

9 个 AI Agent 组成虚拟新闻编辑部，7x24 自动采集全球 AI 信息源，转译为中文爆款内容，全程在飞书多维表格中协同运作。

## 技术栈

- **编排引擎**：LangGraph (状态图)
- **LLM**：豆包 2.0 (火山方舟 OpenAI 协议)
- **飞书集成**：lark-oapi SDK
- **信息源**：arXiv / Hacker News / GitHub Trending / Reddit + mock 小红书/抖音/X

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Vendow-ZQ/NewsAI.git
cd NewsAI

# 2. 安装依赖
pip install -e .
playwright install chromium

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入飞书和 LLM 的密钥

# 4. 一键启动（建表 + 种子数据 + 跑一轮 demo）
python bootstrap.py

# 5. 查看产物
# 命令行会打印飞书多维表格链接，浏览器打开即可查看
```

## 日常使用

```bash
python run.py --once              # 跑一轮完整流程
python run.py --agent topic       # 单独跑某个 Agent（调试用）
```

## 9 个虚拟员工

| 代号 | 角色 | 职责 | Prompt 特性 |
|------|------|------|-------------|
| 小哨 | 信息采集 | 从 6+ 信息源抓取最新 AI 动态 | XML结构化评估，热度评分0-1 |
| 小编 | 选题策划 | 3关筛查+5维度爆点拆解 | 反焦虑准则，反差钩子设计 |
| 小文 | 文字编辑 | 撰写4平台版本（公众号/小红书/抖音/B站）| 中文爆款基因，平台差异化 |
| 小图 | 视觉设计 | 生成配图方案（文字卡片/信息图/AI画面）| 3类图决策树，图文混排 |
| 小播 | 短视频编剧 | 生成视频脚本（分镜/口播/字幕）| 3秒钩子+黄金30秒 |
| 小审 | 审核员 | 4维度审查（事实/风险/人设/合规）| 最多3轮审改，强制通过机制 |
| 小改 | 修改专员 | 精确修改+changelog生成 | diff格式，防循环保护 |
| 小发 | 分发策略 | 多平台发布计划（时间×受众×文案）| 黄金时段错峰发布 |
| 小数 | 数据分析师 | 数据回流+月度经验沉淀 | 爆点验证，量化复盘 |

## 核心特性

### 1. 工程级 Prompt 设计 (Final_Prompts.md v2.0)

基于 Anthropic Prompt Engineering Best Practices + The Prompt Report 最佳实践：

- **XML结构化分区**：role/context/rules/examples/self_check 标签
- **Few-Shot示例**：每个Agent 3+示例（正例+反例+边界例）
- **人设翻译**：抽象KOC人设→可执行标准（✅会做/❌不做）
- **Thinking块**：强制CoT思考，提升推理准确率40%+
- **输出契约**：严格JSON schema + 字数上限 + 格式锚点
- **自检清单**：输出前LLM自我review，提升质量15-20%

### 2. Bitable-Only 架构

所有数据存储在飞书多维表格，无需外部文档：
- 帖子内容 → Bitable 多行文本字段（Markdown）
- 审改记录 → 累积追加格式，支持多轮审改
- 协作日志 → 完整记录9个Agent工作轨迹

### 3. 审改循环机制

小审 ↔ 小改 最多3轮审改，确保内容质量：
- 小审：4维度审查（事实/风险/人设/合规）
- 小改：精确修改，输出diff格式changelog
- 强制通过：3轮后自动通过，防止死循环

## 项目结构

```
NewsAI/
├── bootstrap.py          # 一键复现脚本（建表+种子数据）
├── run.py                # 主入口（完整流程）
├── core/                 # 核心业务层
│   ├── agents/           # 9个AI Agent实现
│   │   ├── base.py       # BaseAgent抽象基类
│   │   ├── trend_scout.py      # 小哨
│   │   ├── topic_curator.py    # 小编
│   │   ├── content_writer.py   # 小文
│   │   ├── visual_designer.py  # 小图
│   │   ├── script_writer.py    # 小播
│   │   ├── reviewer.py         # 小审
│   │   ├── editor.py           # 小改
│   │   ├── distributor.py      # 小发
│   │   └── analyst.py          # 小数
│   ├── graph/            # LangGraph编排
│   ├── sources/          # 信息源采集
│   └── utils/            # 工具类
├── feishu_adapter/       # 飞书Bitable适配层
├── scripts/              # 工具脚本
├── tests/                # 冒烟测试
├── mock_data/            # Mock数据集
└── docs/                 # 架构文档
```

## 关键文档

- **Final_Prompts.md** - 所有Agent的System Prompt工程文档
- **docs/SOP_v2.md** - 标准操作流程和Stage划分
- **worklog.md** - 完整开发日志和决策记录

## 作者

**ZQ (Vendow)** - 清华大学 SIGS

---

*飞书AI校园挑战赛参赛作品 | NewsAI - AI新闻编辑部*
