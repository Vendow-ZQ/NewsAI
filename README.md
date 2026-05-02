# NewsAI - AI 新闻编辑部

**飞书 AI 校园挑战赛参赛作品**
>跑在飞书多维表格上的 AI 新闻编辑部

## 一句话介绍

9 个 AI Agent 组成虚拟新闻编辑部，7x24 自动采集全球 AI 信息源，转译为中文爆款内容，全程在飞书多维表格中协同运作。

## 技术栈

- **编排引擎**：LangGraph (状态图)
- **LLM**：豆包 1.6 (火山方舟 OpenAI 协议)
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

| 代号 | 角色 | 职责 |
|------|------|------|
| 小哨 | 信息采集 | 从 4+ 信息源抓取最新 AI 动态 |
| 小析 | 爆点分析 | 评估新闻的传播潜力与爆点 |
| 小编 | 选题生成 | 根据爆点排序生成选题方案 |
| 小文 | 文字编辑 | 撰写适配不同平台的中文内容 |
| 小图 | 视觉设计 | 生成文字卡片/信息图/AI 配图 |
| 小播 | 短视频编剧 | 生成短视频脚本与分镜 |
| 小审 | 审核员 | 事实核查与合规审核 |
| 小发 | 分发策略 | 规划多平台分发方案 |
| 小数 | 数据分析 | 复盘内容表现并优化策略 |

## 项目结构

```
NewsAI/
├── bootstrap.py          # 一键复现脚本
├── run.py                # 主入口
├── core/                 # 核心业务层（Agent / Graph / Sources）
├── feishu_adapter/       # 飞书多维表格适配层
├── mock_data/            # Mock 数据集
├── tests/                # 冒烟测试
└── docs/                 # 架构文档
```

详细技术方案见 [WORKSPACE.md](WORKSPACE.md)，产品方案见 [PROJECT.md](PROJECT.md)。

## 作者

ZQ (Vendow) - 清华大学 SIGS
