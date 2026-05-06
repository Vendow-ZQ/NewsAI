# NewsAI 快速运转指南

## 🚀 一键启动（推荐）

### 步骤1：环境检查
```bash
# 检查Python版本（需3.8+）
python --version

# 检查依赖是否安装
pip list | findstr lark-oapi
pip list | findstr langgraph
pip list | findstr loguru
```

### 步骤2：配置环境变量
```bash
# 复制示例文件
copy .env.example .env

# 编辑 .env 文件，填写以下信息
LARK_APP_ID=你的飞书应用ID
LARK_APP_SECRET=你的飞书应用密钥
LARK_BASE_APP_TOKEN=你的BaseToken（可选，bootstrap会提示创建）
ARK_API_KEY=你的豆包API密钥
```

### 步骤3：一键初始化（只需运行一次）
```bash
python bootstrap.py
```

**这个脚本会做什么：**
1. 检查环境变量
2. 连接飞书Base
3. 创建7张表（信源配置/热帖库/选题库/数据库/KOC人设/Agent花名册/Agent协作日志）
4. 插入27条种子数据
5. 打印Base链接

### 步骤4：运行完整流程
```bash
# 方式1：跑一轮完整流程
python run.py --once

# 方式2：指定选题ID运行
python run.py --once --topic TOPIC-20260507-001

# 方式3：单独运行某个Agent（调试用）
python run.py --agent trend    # 只运行小哨
python run.py --agent topic    # 只运行小编
python run.py --agent review   # 只运行小审
```

---

## 📋 分步运转（排查用）

### 第1步：检查飞书连接
```bash
python -c "from core.utils.feishu_base import FeishuBaseManager; bm = FeishuBaseManager(); print('连接成功' if bm.app_token else '连接失败')"
```

### 第2步：检查表是否创建
```bash
# 查看Base中有哪些表
python -c "
from core.utils.feishu_base import FeishuBaseManager
bm = FeishuBaseManager()
tables = bm.list_tables()
for t in tables:
    print(f'{t.name}: {t.table_id}')
"
```

### 第3步：检查种子数据
```bash
# 查看热帖库有多少条记录
python -c "
from feishu_adapter.feishu_storage import FeishuStorage
storage = FeishuStorage()
posts = storage.query('trend', limit=5)
print(f'热帖库有 {len(posts)} 条记录')
for p in posts[:3]:
    print(f'  - {p.get(\"id\")}: {p.get(\"标题\", \"\")[:30]}')
"
```

### 第4步：手动触发小哨采集
```bash
python -c "
import asyncio
from core.agents.trend_scout import TrendScoutAgent
from feishu_adapter.feishu_storage import FeishuStorage

async def test():
    storage = FeishuStorage()
    agent = TrendScoutAgent(storage, None)
    result = await agent.execute({})
    print(f'采集完成: {result}')

asyncio.run(test())
"
```

---

## 🔧 常见问题排查

### 问题1：编码错误（中文乱码）
```bash
# PowerShell中设置UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 或者在命令前加chcp
chcp 65001
python run.py --once
```

### 问题2：模块导入错误
```bash
# 确保在项目根目录
cd D:\Code\NewsAI

# 安装依赖
pip install -e .
```

### 问题3：飞书权限错误（91403）
```bash
# 检查应用是否有Base权限
# 1. 登录飞书开放平台
# 2. 进入应用管理
# 3. 添加权限：bitable:record（读取/写入/更新记录）
# 4. 重新获取app_token
```

### 问题4：LLM超时
```bash
# 编辑 core/llm/client.py
# 增加超时时间：timeout=300（默认120秒可能不够）
```

---

## 📊 正常运转的标志

### 成功运行bootstrap.py后：
```
✅ 环境检查通过
✅ 已连接飞书Base: https://base.feishu.cn/xxx
✅ 创建表成功: src_sources
✅ 创建表成功: trend_hotposts
✅ 创建表成功: topic_posts
✅ 创建表成功: data_analytics
✅ 创建表成功: koc_profile
✅ 创建表成功: agent_roster
✅ 创建表成功: agent_logs
✅ 插入种子数据: 27条

🎉 初始化完成！Base链接: https://base.feishu.cn/xxx
```

### 成功运行run.py后：
```
开始一轮完整流程...
执行图流程，选题ID: 未指定
小哨采集完成: 5条热帖
小编策划完成: 2条选题
小文生产完成: 2条帖子内容
小图生产完成: 2套配图方案
小播生产完成: 2条视频脚本
小审审查完成: 2条通过
小发生产完成: 2条分发计划
小数分析完成: 2条数据回流
流程完成
```

---

## 🎯 日常使用流程

### 场景1：每日自动运行
```bash
# Windows定时任务
schtasks /create /tn "NewsAI_Daily" /tr "python D:\Code\NewsAI\run.py --once" /sc daily /st 09:00
```

### 场景2：查看运行日志
```bash
# 查看最后100行日志
tail -n 100 last_run.log

# PowerShell
cat last_run.log | Select-Object -Last 100
```

### 场景3：清理数据重新来过
```bash
# 删除所有表数据（危险！）
python scripts/cleanup_base.py

# 然后重新初始化
python bootstrap.py
```

---

## 🆘 紧急救援

如果完全不工作，用最小化测试：
```bash
# 测试1：Python环境
python -c "print('Python OK')"

# 测试2：依赖安装
python -c "import langgraph; print('LangGraph OK')"
python -c "from core.utils.feishu_base import FeishuBaseManager; print('FeishuBase OK')"

# 测试3：飞书连接
python tests/test_lark_hello.py

# 测试4：LLM连接
python tests/test_doubao_hello.py

# 测试5：单Agent
python run.py --agent trend
```

---

## 📞 求助信息

如果还是无法运转，收集以下信息：
1. `python --version`
2. `pip list` 的输出
3. `.env` 文件内容（脱敏后）
4. 运行时的完整错误截图
5. `last_run.log` 的最后50行

**项目文档**: https://github.com/Vendow-ZQ/NewsAI
**提交文档**: docs/ByteIntern_Submission.md
